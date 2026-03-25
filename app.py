# -*- coding: utf-8 -*-
"""
财神日历 Flask 后端
依赖: flask, lunar-python, flask-cors
运行: python app.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lunar_python import Lunar, Solar
import datetime
import os

app = Flask(__name__, static_folder="static", template_folder=".")
CORS(app)

# ──────────────────────────────────────────────
# 基础数据常量
# ──────────────────────────────────────────────

GAN  = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
ZHI  = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

GAN_INFO = {
    "甲":("木","阳"),"乙":("木","阴"),
    "丙":("火","阳"),"丁":("火","阴"),
    "戊":("土","阳"),"己":("土","阴"),
    "庚":("金","阳"),"辛":("金","阴"),
    "壬":("水","阳"),"癸":("水","阴"),
}

NAYIN = [
    "海中金","炉中火","大林木","路旁土","剑锋金",
    "山头火","涧下水","城头土","白蜡金","杨柳木",
    "泉中水","屋上土","霹雳火","松柏木","长流水",
    "砂中金","山下火","平地木","壁上土","金箔金",
    "覆灯火","天河水","大驿土","钗钏金","桑柘木",
    "大溪水","沙中土","天上火","石榴木","大海水",
]

WUXING_SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
WUXING_KE   = {"木":"土","土":"水","水":"火","火":"金","金":"木"}

GAN_HE = {
    ("甲","己"):"土",("己","甲"):"土",
    ("乙","庚"):"金",("庚","乙"):"金",
    ("丙","辛"):"水",("辛","丙"):"水",
    ("丁","壬"):"木",("壬","丁"):"木",
    ("戊","癸"):"火",("癸","戊"):"火",
}

GAN_CHONG = {
    ("甲","庚"),("庚","甲"),("乙","辛"),("辛","乙"),
    ("丙","壬"),("壬","丙"),("丁","癸"),("癸","丁"),
}

CHONG_PAIRS = {
    ("子","午"),("午","子"),("丑","未"),("未","丑"),
    ("寅","申"),("申","寅"),("卯","酉"),("酉","卯"),
    ("辰","戌"),("戌","辰"),("巳","亥"),("亥","巳"),
}

HE_PAIRS = {
    ("子","丑"),("丑","子"),("寅","亥"),("亥","寅"),
    ("卯","戌"),("戌","卯"),("辰","酉"),("酉","辰"),
    ("巳","申"),("申","巳"),("午","未"),("未","午"),
}

SANHE_GROUPS = [
    {"申","子","辰"},{"亥","卯","未"},
    {"寅","午","戌"},{"巳","酉","丑"},
]

HAI_PAIRS = {
    ("子","未"),("未","子"),("丑","午"),("午","丑"),
    ("寅","巳"),("巳","寅"),("卯","辰"),("辰","卯"),
    ("申","亥"),("亥","申"),("酉","戌"),("戌","酉"),
}

PO_PAIRS = {
    ("子","酉"),("酉","子"),("卯","午"),("午","卯"),
    ("辰","丑"),("丑","辰"),("未","戌"),("戌","未"),
    ("寅","亥"),("亥","寅"),("巳","申"),("申","巳"),
}

XING_GROUPS = [{"寅","巳","申"},{"丑","未","戌"}]
XING_PAIRS  = {("子","卯"),("卯","子")}
ZI_XING     = {"辰","午","酉","亥"}

SANHUI_GROUPS = [
    ({"寅","卯","辰"},"木"),
    ({"巳","午","未"},"火"),
    ({"申","酉","戌"},"金"),
    ({"亥","子","丑"},"水"),
]

CANG_GAN = {
    "子":["癸"],
    "丑":["己","癸","辛"],
    "寅":["甲","丙","戊"],
    "卯":["乙"],
    "辰":["戊","乙","癸"],
    "巳":["丙","庚","戊"],
    "午":["丁","己"],
    "未":["己","丁","乙"],
    "申":["庚","壬","戊"],
    "酉":["辛"],
    "戌":["戊","辛","丁"],
    "亥":["壬","甲"],
}

SHI_CHEN_LABELS = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
SHI_CHEN_NAMES  = ["子时","丑时","寅时","卯时","辰时","巳时","午时","未时","申时","酉时","戌时","亥时"]
SHI_CHEN_RANGES = {
    "子":"23:00–00:59","丑":"01:00–02:59","寅":"03:00–04:59",
    "卯":"05:00–06:59","辰":"07:00–08:59","巳":"09:00–10:59",
    "午":"11:00–12:59","未":"13:00–14:59","申":"15:00–16:59",
    "酉":"17:00–18:59","戌":"19:00–20:59","亥":"21:00–22:59",
}

# 简化版时辰神煞（按十二地支顺序：子丑寅卯辰巳午未申酉戌亥）
TIANSHEN_LIST = [
    "青龙","明堂","天刑","朱雀","金匮","天德",
    "白虎","玉堂","天牢","玄武","司命","勾陈",
]
TIANSHEN_LUCK = {
    "青龙":"吉","明堂":"吉","天刑":"凶","朱雀":"凶","金匮":"吉","天德":"吉",
    "白虎":"凶","玉堂":"吉","天牢":"凶","玄武":"凶","司命":"吉","勾陈":"凶",
}

# 时辰宜忌由 build_basic_hour_table 动态从 lunar_python 获取，不再使用固定表
# 每个时辰的代表时刻（取时辰中间点）
SHI_CHEN_SAMPLE_HOUR = {
    "子": 23, "丑": 1,  "寅": 3,  "卯": 5,
    "辰": 7,  "巳": 9,  "午": 11, "未": 13,
    "申": 15, "酉": 17, "戌": 19, "亥": 21,
}

# 关系解释文案
REL_DESC = {
    "冲":   "冲表示外部刺激、移动、变化与对立增强，适合预留缓冲与备选方案，不宜急推硬压。",
    "合":   "合表示牵引、协商、绑定与整合，适合沟通、对接、合作，但也要防止拖带与牵制。",
    "害":   "害偏向暗耗、误会、不对称摩擦，宜提前澄清信息，避免口舌与模糊承诺。",
    "破":   "破偏向结构性破口、节奏被打断与计划走样，关键事项应留冗余。",
    "刑":   "刑偏向规则压力、约束、内耗或情绪紧张，宜按流程办事，避免强行顶撞。",
    "三合": "三合表示聚势成局，利于整合资源、形成共识与推进联合事项。",
    "三会": "三会表示同一气势汇聚，利于顺势推进长期主线与系统性工作。",
    "同气": "同气表示同频共振，利于延续与复盘，但也要避免因惯性而迟滞。",
    "天干合":"天干合表示牵引协调，双方有整合、合作与互助的倾向。",
    "天干冲":"天干冲表示方向对立、外部张力明显，宜保持弹性、预留回旋空间。",
}

SHISHEN_KEYWORDS = {
    "正官":"责任、规则与压力",
    "七杀":"责任、规则与压力",
    "正财":"资源、效率与现实事务",
    "偏财":"资源、效率与现实事务",
    "正印":"支持、学习与修复",
    "偏印":"支持、学习与修复",
    "食神":"表达、输出与创意",
    "伤官":"表达、输出与创意",
    "比肩":"自我主张与同侪互动",
    "劫财":"自我主张与同侪互动",
}

# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def gz_idx(gz):
    """干支 → 60甲子序号（0-59）"""
    g, z = gz[0], gz[1]
    gi = GAN.index(g)
    zi = ZHI.index(z)
    for i in range(60):
        if i % 10 == gi and i % 12 == zi:
            return i
    return 0

def nayin_of(gz):
    idx = gz_idx(gz)
    return NAYIN[idx // 2]

def wuxing_of_gan(g):
    return GAN_INFO.get(g, ("?","?"))[0]

def yinyang_of_gan(g):
    return GAN_INFO.get(g, ("?","?"))[1]

def ten_god(day_master, target):
    """以 day_master 天干为日主，计算 target 天干的十神"""
    dm_wx = wuxing_of_gan(day_master)
    tg_wx = wuxing_of_gan(target)
    dm_yy = yinyang_of_gan(day_master)
    tg_yy = yinyang_of_gan(target)
    same_yy = (dm_yy == tg_yy)

    if dm_wx == tg_wx:
        return "比肩" if same_yy else "劫财"
    if WUXING_SHENG.get(dm_wx) == tg_wx:
        return "食神" if same_yy else "伤官"
    if WUXING_SHENG.get(tg_wx) == dm_wx:
        return "偏印" if same_yy else "正印"
    if WUXING_KE.get(dm_wx) == tg_wx:
        return "偏财" if same_yy else "正财"
    if WUXING_KE.get(tg_wx) == dm_wx:
        return "七杀" if same_yy else "正官"
    return "未知"

def zhi_relations(a, b):
    """返回地支 a 与 b 的关系列表"""
    rels = []
    if a == b:
        rels.append("同气")
        if a in ZI_XING:
            rels.append("自刑")
        return rels
    if (a, b) in CHONG_PAIRS:
        rels.append("冲")
    if (a, b) in HE_PAIRS:
        rels.append("合")
    if (a, b) in HAI_PAIRS:
        rels.append("害")
    if (a, b) in PO_PAIRS:
        rels.append("破")
    if (a, b) in XING_PAIRS:
        rels.append("刑")
    for g in XING_GROUPS:
        if a in g and b in g and a != b:
            rels.append("刑")
            break
    for g, _ in SANHUI_GROUPS:
        if a in g and b in g and a != b:
            rels.append("三会")
            break
    for g in SANHE_GROUPS:
        if a in g and b in g and a != b:
            rels.append("三合")
            break
    return rels if rels else ["无"]

def gan_relations(a, b):
    rels = []
    if (a, b) in GAN_HE:
        rels.append("天干合")
    if (a, b) in GAN_CHONG:
        rels.append("天干冲")
    return rels

# ──────────────────────────────────────────────
# 黄历核心：从 lunar_python 提取数据
# ──────────────────────────────────────────────

def _lunar_to_day_dict(lunar):
    solar = lunar.getSolar()
    date_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d}"

    weekday_map = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
    wd = datetime.date(solar.getYear(), solar.getMonth(), solar.getDay()).weekday()
    weekday = weekday_map[wd]

    # 农历
    lunar_year  = lunar.getYearInChinese()
    lunar_month = lunar.getMonthInChinese()
    lunar_day   = lunar.getDayInChinese()
    lunar_ymd   = f"{lunar_year}年{lunar_month}月{lunar_day}"

    # 干支
    year_gz  = lunar.getYearInGanZhi()
    month_gz = lunar.getMonthInGanZhi()
    day_gz   = lunar.getDayInGanZhi()
    day_zhi  = day_gz[1] if len(day_gz) >= 2 else day_gz

    # 纳音
    day_nayin = nayin_of(day_gz) if len(day_gz) == 2 else ""

    # 宜忌
    yi_raw = lunar.getDayYi()
    ji_raw = lunar.getDayJi()
    yi = list(yi_raw) if yi_raw else ["祈福","纳财","出行"]
    ji = list(ji_raw) if ji_raw else ["争执","大额借贷"]

    # 冲煞
    try:
        chong = lunar.getDayChong()
        sha   = lunar.getDaySha()
        chong_desc = f"冲({chong})·煞{sha}"
    except Exception:
        chong_desc = ""
        sha = ""

    # 值神 / 建除 / 星宿
    try:
        tianshen      = lunar.getDayTianShen()
        tianshen_luck = lunar.getDayTianShenLuck() or TIANSHEN_LUCK.get(tianshen, "")
    except Exception:
        tianshen, tianshen_luck = "", ""
    try:
        zhixing = lunar.getDayZhiXing()
    except Exception:
        zhixing = ""
    try:
        xiu      = lunar.getDayXiu()
        xiu_luck = lunar.getDayXiuLuck() or ""
    except Exception:
        xiu, xiu_luck = "", ""

    # 彭祖百忌
    try:
        pengzu_list = lunar.getDayPengZuGan() + lunar.getDayPengZuZhi()
        pengzu = "、".join(pengzu_list) if pengzu_list else ""
    except Exception:
        pengzu = ""

    # 方位
    try:
        dir_xi     = lunar.getDayPositionXiDesc()
        dir_fu     = lunar.getDayPositionFuDesc()
        dir_cai    = lunar.getDayPositionCaiDesc()
        dir_yanggui= lunar.getDayPositionYangGuiDesc()
        dir_yingui = lunar.getDayPositionYinGuiDesc()
    except Exception:
        dir_xi = dir_fu = dir_cai = dir_yanggui = dir_yingui = ""

    return {
        "date":          date_str,
        "weekday":       weekday,
        "lunar_ymd":     lunar_ymd,
        "year_gz":       year_gz,
        "month_gz":      month_gz,
        "day_gz":        day_gz,
        "day_zhi":       day_zhi,
        "day_nayin":     day_nayin,
        "yi":            yi,
        "ji":            ji,
        "chong_desc":    chong_desc,
        "sha":           sha,
        "tianshen":      tianshen,
        "tianshen_luck": tianshen_luck,
        "zhixing":       zhixing,
        "xiu":           xiu,
        "xiu_luck":      xiu_luck,
        "pengzu":        pengzu,
        "dir": {
            "xi":      dir_xi,
            "fu":      dir_fu,
            "cai":     dir_cai,
            "yanggui": dir_yanggui,
            "yingui":  dir_yingui,
        }
    }

# ──────────────────────────────────────────────
# 基础 12 时辰
# ──────────────────────────────────────────────

def build_basic_hour_table(lunar, day_gz):
    """生成基础 12 时辰表，天神/吉凶/宜忌全部从 lunar_python 动态获取"""
    day_gan_idx = GAN.index(day_gz[0])
    start_gan_map = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8]
    start_gan_idx = start_gan_map[day_gan_idx]

    solar_day = lunar.getSolar()
    yy, mm, dd = solar_day.getYear(), solar_day.getMonth(), solar_day.getDay()

    import datetime as _dt

    table = []
    for i, zhi in enumerate(SHI_CHEN_LABELS):
        gan_idx = (start_gan_idx + i) % 10
        gz = GAN[gan_idx] + zhi

        # 时辰冲
        chong_zhi_idx = (ZHI.index(zhi) + 6) % 12
        chong_zhi = ZHI[chong_zhi_idx]
        chong_d = f"冲{chong_zhi}"

        # 动态获取天神、吉凶、宜忌
        try:
            hh = SHI_CHEN_SAMPLE_HOUR[zhi]
            if zhi == "子":
                prev = _dt.date(yy, mm, dd) - _dt.timedelta(days=1)
                s_hour = Solar.fromYmdHms(prev.year, prev.month, prev.day, hh, 30, 0)
            else:
                s_hour = Solar.fromYmdHms(yy, mm, dd, hh, 30, 0)
            l_hour = s_hour.getLunar()
            ts   = l_hour.getTimeTianShen()
            luck = l_hour.getTimeTianShenLuck() or "平"
            yi_raw = list(l_hour.getTimeYi())
            ji_raw = list(l_hour.getTimeJi())
            yi = [v for v in yi_raw if v != "无"]
            ji = [v for v in ji_raw if v != "无"]
        except Exception:
            ts, luck, yi, ji = "", "平", [], []

        table.append({
            "zhi":        zhi,
            "label":      SHI_CHEN_NAMES[i],
            "range":      SHI_CHEN_RANGES[zhi],
            "gz":         gz,
            "luck":       luck,
            "tianshen":   ts,
            "chong_desc": chong_d,
            "sha":        "",
            "yi":         yi,
            "ji":         ji,
        })
    return table

# ──────────────────────────────────────────────
# 八字计算（方式A：阳历推算）
# ──────────────────────────────────────────────

def calc_bazi_from_birth(birth_iso):
    """从阳历出生时间推算四柱，birth_iso 格式：YYYY-MM-DD HH:MM 或 YYYY-MM-DDTHH:MM"""
    birth_iso = birth_iso.replace("T", " ")
    parts = birth_iso.strip().split(" ")
    date_part = parts[0]
    time_part = parts[1] if len(parts) > 1 else "00:00"
    yy, mm, dd = [int(x) for x in date_part.split("-")]
    hh = int(time_part.split(":")[0])
    minute = int(time_part.split(":")[1]) if ":" in time_part else 0

    solar = Solar.fromYmdHms(yy, mm, dd, hh, minute, 0)
    lunar = solar.getLunar()
    eightChar = lunar.getEightChar()

    def pillar_info(gz):
        if not gz or len(gz) < 2:
            return {"gz":gz,"gan":"","zhi":"","nayin":"","wuxing":""}
        g, z = gz[0], gz[1]
        ny = nayin_of(gz)
        wx = wuxing_of_gan(g)
        return {"gz":gz,"gan":g,"zhi":z,"nayin":ny,"wuxing":wx}

    year_gz  = eightChar.getYearGan()  + eightChar.getYearZhi()
    month_gz = eightChar.getMonthGan() + eightChar.getMonthZhi()
    day_gz   = eightChar.getDayGan()   + eightChar.getDayZhi()
    time_gz  = eightChar.getTimeGan()  + eightChar.getTimeZhi()

    return {
        "mode":      "birth",
        "birth_iso": birth_iso,
        "year":  pillar_info(year_gz),
        "month": pillar_info(month_gz),
        "day":   pillar_info(day_gz),
        "time":  pillar_info(time_gz),
    }

# ──────────────────────────────────────────────
# 八字处理（方式B：手动输入）
# ──────────────────────────────────────────────

def build_bazi_manual(year_gz, month_gz, day_gz, time_gz):
    def pillar_info(gz):
        if not gz or len(gz) < 2:
            return {"gz":gz,"gan":"","zhi":"","nayin":None,"wuxing":None}
        return {"gz":gz,"gan":gz[0],"zhi":gz[1],"nayin":None,"wuxing":None}
    return {
        "mode":  "manual",
        "year":  pillar_info(year_gz),
        "month": pillar_info(month_gz),
        "day":   pillar_info(day_gz),
        "time":  pillar_info(time_gz),
    }

# ──────────────────────────────────────────────
# 个性化分析
# ──────────────────────────────────────────────

def build_personal(day_data, bazi):
    """生成个性化分析数据"""
    day_master = bazi["day"]["gan"]  # 日主天干

    user_zhis = [
        bazi["year"]["zhi"],
        bazi["month"]["zhi"],
        bazi["day"]["zhi"],
        bazi["time"]["zhi"],
    ]
    user_zhi_labels = ["年支","月支","日支","时支"]
    user_gans = [
        bazi["year"]["gan"],
        bazi["month"]["gan"],
        bazi["day"]["gan"],
        bazi["time"]["gan"],
    ]
    user_gan_labels = ["年干","月干","日干","时干"]

    flow_levels = [
        ("流年", day_data["year_gz"]),
        ("流月", day_data["month_gz"]),
        ("流日", day_data["day_gz"]),
    ]

    # ── 天干关系 ──────────────────────────────
    gan_relations_list = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2:
            continue
        fg = level_gz[0]
        tg_shishen = ten_god(day_master, fg) if day_master else ""
        for ug, ul in zip(user_gans, user_gan_labels):
            if not ug:
                continue
            rels = gan_relations(fg, ug)
            for r in rels:
                gan_relations_list.append({
                    "level":    level_name,
                    "flow_gan": fg,
                    "user_gan": ug,
                    "user_label": ul,
                    "rel":      r,
                    "desc":     REL_DESC.get(r, ""),
                    "ten_god":  tg_shishen,
                })

    # ── 地支关系 ──────────────────────────────
    zhi_relations_list = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2:
            continue
        fz = level_gz[1]
        for uz, ul in zip(user_zhis, user_zhi_labels):
            if not uz:
                continue
            rels = zhi_relations(fz, uz)
            if rels and rels != ["无"]:
                for r in rels:
                    zhi_relations_list.append({
                        "level":     level_name,
                        "flow_zhi":  fz,
                        "user_zhi":  uz,
                        "user_label":ul,
                        "rel":       r,
                        "desc":      REL_DESC.get(r, ""),
                    })

    # ── 藏干十神 ──────────────────────────────
    cang_gan_analysis = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2:
            continue
        fz = level_gz[1]
        cg_list = CANG_GAN.get(fz, [])
        shishen_list = []
        for cg in cg_list:
            ss = ten_god(day_master, cg) if day_master else ""
            shishen_list.append({"gan": cg, "ten_god": ss, "keyword": SHISHEN_KEYWORDS.get(ss, "")})
        cang_gan_analysis.append({
            "level":   level_name,
            "flow_gz": level_gz,
            "flow_zhi":fz,
            "cang_gan": shishen_list,
        })

    # ── 十神汇总（流年/月/日天干对日主）──────
    flow_ten_gods = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2:
            continue
        fg = level_gz[0]
        ss = ten_god(day_master, fg) if day_master else ""
        flow_ten_gods.append({
            "level":   level_name,
            "flow_gz": level_gz,
            "flow_gan":fg,
            "ten_god": ss,
            "keyword": SHISHEN_KEYWORDS.get(ss, ""),
        })

    # ── 总结生成 ──────────────────────────────
    support_rels = {"合","三合","三会","同气","天干合"}
    conflict_rels = {"冲","刑","害","破","天干冲"}

    has_support  = any(r["rel"] in support_rels  for r in zhi_relations_list + gan_relations_list)
    has_conflict = any(r["rel"] in conflict_rels for r in zhi_relations_list + gan_relations_list)

    if has_support and not has_conflict:
        summary_base = "今日与你命局之间以协同关系为主，整体顺势，适合沟通、整合资源、推进既定事项。"
    elif has_conflict and not has_support:
        summary_base = "今日与你命局之间以刺激性关系为主，变化与压力感较明显，重要事项宜放慢节奏并预留缓冲。"
    elif has_support and has_conflict:
        summary_base = "今日同时存在助力与牵制两类关系，宜稳中求进，借力顺势的同时注意节奏管控。"
    else:
        summary_base = "今日与你命局整体互动偏中性，按既定节奏执行、保持稳定即可。"

    yi_list = day_data.get("yi", [])
    ji_list = day_data.get("ji", [])
    if yi_list:
        summary_base += f"若结合黄历，优先安排「{'、'.join(yi_list[:2])}」类事项会更稳妥。"
    if ji_list:
        summary_base += f"对「{'、'.join(ji_list[:2])}」类事项则应更加谨慎。"

    # ── 行动建议 ──────────────────────────────
    action_points = []
    conflict_items = [r for r in zhi_relations_list if r["rel"] in conflict_rels]
    if conflict_items:
        descs = [f"{r['level']}地支{r['flow_zhi']}{r['rel']}你的{r['user_label']}" for r in conflict_items[:3]]
        action_points.append("重点关注：" + "；".join(descs) + "。")
    support_items = [r for r in zhi_relations_list if r["rel"] in support_rels]
    if support_items:
        descs = [f"{r['level']}地支{r['flow_zhi']}{r['rel']}你的{r['user_label']}" for r in support_items[:3]]
        action_points.append("可借力点：" + "；".join(descs) + "。")
    if flow_ten_gods:
        tg_descs = [f"{t['level']}天干为{t['flow_gan']}，对日主属「{t['ten_god']}（{t['keyword']}）」" for t in flow_ten_gods]
        action_points.append("十神角度：" + "；".join(tg_descs) + "。")
    if yi_list:
        action_points.append(f"今日宜优先考虑：{'、'.join(yi_list[:3])}。")
    if ji_list:
        action_points.append(f"今日忌需谨慎对待：{'、'.join(ji_list[:2])}。")

    # ── 个性化宜忌 ────────────────────────────
    SHISHEN_YI = {
        "正财":"理财·收款·签约",   "偏财":"投资·开拓·进财",
        "正官":"办公务·见长辈·规范流程", "七杀":"主动出击·处理竞争",
        "正印":"学习·求助·修复关系",  "偏印":"研究·独处·创作",
        "食神":"表达·展示·社交输出",  "伤官":"创新·突破·艺术",
        "比肩":"合作·同侪互助·坚守立场","劫财":"主动争取·独立行动",
    }
    SHISHEN_JI = {
        "正财":"冲动消费·乱花钱", "偏财":"投机冒险·不实之财",
        "正官":"违规·拖延公务",  "七杀":"逃避压力·拖延决策",
        "正印":"急于求成·忽视细节","偏印":"过度封闭·拒绝沟通",
        "食神":"压抑情绪·不表达", "伤官":"破坏规则·言语冒失",
        "比肩":"争执·固执己见",  "劫财":"冲动消费·意气用事",
    }
    personal_yi_set = []
    personal_ji_set = []
    for r in zhi_relations_list:
        if r["rel"] in support_rels:
            personal_yi_set.append(f"借{r['level']}之力·{r['user_label']}顺势")
        elif r["rel"] in conflict_rels:
            personal_ji_set.append(f"慎防{r['level']}冲{r['user_label']}·避免强行推进")
    day_flow_tg = next((t for t in flow_ten_gods if t["level"] == "流日"), None)
    if day_flow_tg and day_flow_tg["ten_god"]:
        tg = day_flow_tg["ten_god"]
        if tg in SHISHEN_YI:
            personal_yi_set.append(SHISHEN_YI[tg])
        if tg in SHISHEN_JI:
            personal_ji_set.append(SHISHEN_JI[tg])
    if not personal_yi_set:
        personal_yi_set = list(yi_list[:4])
    if not personal_ji_set:
        personal_ji_set = list(ji_list[:3])

    return {
        "day_master":       day_master,
        "gan_relations":    gan_relations_list,
        "zhi_relations":    zhi_relations_list,
        "cang_gan_analysis":cang_gan_analysis,
        "flow_ten_gods":    flow_ten_gods,
        "summary":          summary_base,
        "action_points":    action_points,
        "personal_yi":      personal_yi_set,
        "personal_ji":      personal_ji_set,
    }

# ──────────────────────────────────────────────
# 个性化 12 时辰
# ──────────────────────────────────────────────

def build_personal_hour_table(basic_table, bazi):
    day_master = bazi["day"]["gan"]
    user_zhis  = [bazi["year"]["zhi"], bazi["month"]["zhi"], bazi["day"]["zhi"], bazi["time"]["zhi"]]
    user_labels= ["年支","月支","日支","时支"]

    SUPPORT_RELS  = {"合","三合","三会","同气"}
    CONFLICT_RELS = {"冲","刑","害","破"}

    HOUR_TG_YI = {
        "正财":"收款·谈钱", "偏财":"主动开拓",
        "正官":"办正事·见领导", "七杀":"主动出击",
        "正印":"学习·休养", "偏印":"独处·研究",
        "食神":"社交·表达", "伤官":"创新·突破",
        "比肩":"合作·商议", "劫财":"独立行动",
    }
    HOUR_TG_JI = {
        "正财":"冲动花钱", "偏财":"冒险投机",
        "正官":"违规拖延", "七杀":"逃避压力",
        "正印":"急于求成", "偏印":"过度封闭",
        "食神":"压抑情绪", "伤官":"言语冒失",
        "比肩":"争执固执", "劫财":"意气用事",
    }

    result = []
    for hour in basic_table:
        gz  = hour["gz"]
        zhi = hour["zhi"]
        hg  = gz[0] if gz else ""
        tg = ten_god(day_master, hg) if (day_master and hg) else ""
        rels = []
        for uz, ul in zip(user_zhis, user_labels):
            if not uz:
                continue
            rs = zhi_relations(zhi, uz)
            if rs and rs != ["无"]:
                for r in rs:
                    rels.append({"with": ul, "type": r})

        rel_types = {r["type"] for r in rels}
        if rel_types & SUPPORT_RELS and not (rel_types & CONFLICT_RELS):
            personal_luck = "吉"
        elif rel_types & CONFLICT_RELS:
            personal_luck = "凶"
        else:
            personal_luck = hour["luck"]

        hour_yi = []
        hour_ji = []
        if rel_types & SUPPORT_RELS:
            hour_yi.append("借合力·顺势推进")
        if rel_types & CONFLICT_RELS:
            hour_ji.append("慎防冲刑·避免强推")
        if tg in HOUR_TG_YI:
            hour_yi.append(HOUR_TG_YI[tg])
        if tg in HOUR_TG_JI:
            hour_ji.append(HOUR_TG_JI[tg])
        if not hour_yi:
            hour_yi = list(hour.get("yi", []))
        if not hour_ji:
            hour_ji = list(hour.get("ji", []))

        h = dict(hour)
        h["personal"] = {
            "ten_god": tg,
            "relations": rels,
            "luck": personal_luck,
            "yi": hour_yi,
            "ji": hour_ji,
        }
        result.append(h)
    return result

# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "calendar.html")

@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/api/day", methods=["POST"])
def api_day():
    data = request.get_json(force=True) or {}
    date_str = data.get("date", "")
    try:
        yy, mm, dd = [int(x) for x in date_str.split("-")]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    day_data  = _lunar_to_day_dict(lunar)
    hour_table= build_basic_hour_table(lunar, day_data["day_gz"])

    return jsonify({"day": day_data, "basic_hour_table": hour_table})

@app.route("/api/personal_day_birth", methods=["POST"])
def api_personal_day_birth():
    data = request.get_json(force=True) or {}
    date_str  = data.get("date", "")
    birth_iso = data.get("birth", "")

    try:
        yy, mm, dd = [int(x) for x in date_str.split("-")]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        return jsonify({"error": f"日期解析失败: {e}"}), 400

    try:
        bazi = calc_bazi_from_birth(birth_iso)
    except Exception as e:
        return jsonify({"error": f"八字计算失败: {e}"}), 400

    day_data   = _lunar_to_day_dict(lunar)
    basic_table= build_basic_hour_table(lunar, day_data["day_gz"])
    personal   = build_personal(day_data, bazi)
    pers_table = build_personal_hour_table(basic_table, bazi)

    return jsonify({
        "bazi":                bazi,
        "day":                 day_data,
        "basic_hour_table":    basic_table,
        "personal":            personal,
        "personal_hour_table": pers_table,
    })

@app.route("/api/personal_day_manual", methods=["POST"])
def api_personal_day_manual():
    data = request.get_json(force=True) or {}
    date_str = data.get("date", "")
    bazi_raw = data.get("bazi", {})

    try:
        yy, mm, dd = [int(x) for x in date_str.split("-")]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        return jsonify({"error": f"日期解析失败: {e}"}), 400

    # 校验输入
    required_keys = ["year_gz","month_gz","day_gz","time_gz"]
    for k in required_keys:
        gz = bazi_raw.get(k, "")
        if len(gz) != 2:
            return jsonify({"error": f"{k} 必须是2个字（天干+地支），当前：{gz}"}), 400
        if gz[0] not in GAN:
            return jsonify({"error": f"{k} 第一个字必须是天干，当前：{gz[0]}"}), 400
        if gz[1] not in ZHI:
            return jsonify({"error": f"{k} 第二个字必须是地支，当前：{gz[1]}"}), 400

    bazi = build_bazi_manual(
        bazi_raw["year_gz"], bazi_raw["month_gz"],
        bazi_raw["day_gz"],  bazi_raw["time_gz"],
    )

    day_data   = _lunar_to_day_dict(lunar)
    basic_table= build_basic_hour_table(lunar, day_data["day_gz"])
    personal   = build_personal(day_data, bazi)
    pers_table = build_personal_hour_table(basic_table, bazi)

    return jsonify({
        "bazi":                bazi,
        "day":                 day_data,
        "basic_hour_table":    basic_table,
        "personal":            personal,
        "personal_hour_table": pers_table,
    })

# 为 index.html（主站）提供静态文件服务
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
