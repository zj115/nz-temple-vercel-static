# -*- coding: utf-8 -*-
"""
财神日历共用逻辑 — 供 Vercel Serverless Functions 调用
所有数据常量、工具函数、核心计算函数均在此文件
"""

from lunar_python import Lunar, Solar
import datetime

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

SHI_CHEN_SAMPLE_HOUR = {
    "子": 23, "丑": 1,  "寅": 3,  "卯": 5,
    "辰": 7,  "巳": 9,  "午": 11, "未": 13,
    "申": 15, "酉": 17, "戌": 19, "亥": 21,
}

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
# 黄历核心
# ──────────────────────────────────────────────

def _lunar_to_day_dict(lunar):
    solar = lunar.getSolar()
    date_str = f"{solar.getYear()}-{solar.getMonth():02d}-{solar.getDay():02d}"
    weekday_map = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
    wd = datetime.date(solar.getYear(), solar.getMonth(), solar.getDay()).weekday()
    weekday = weekday_map[wd]
    lunar_year  = lunar.getYearInChinese()
    lunar_month = lunar.getMonthInChinese()
    lunar_day   = lunar.getDayInChinese()
    lunar_ymd   = f"{lunar_year}年{lunar_month}月{lunar_day}"
    year_gz  = lunar.getYearInGanZhi()
    month_gz = lunar.getMonthInGanZhi()
    day_gz   = lunar.getDayInGanZhi()
    day_zhi  = day_gz[1] if len(day_gz) >= 2 else day_gz
    day_nayin = nayin_of(day_gz) if len(day_gz) == 2 else ""
    yi_raw = lunar.getDayYi()
    ji_raw = lunar.getDayJi()
    yi = list(yi_raw) if yi_raw else ["祈福","纳财","出行"]
    ji = list(ji_raw) if ji_raw else ["争执","大额借贷"]
    try:
        chong = lunar.getDayChong()
        sha   = lunar.getDaySha()
        chong_desc = f"冲({chong})·煞{sha}"
    except Exception:
        chong_desc = ""
        sha = ""
    try:
        tianshen      = lunar.getDayTianShen()
        tianshen_luck = lunar.getDayTianShenLuck() or ""
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
    try:
        pengzu_list = lunar.getDayPengZuGan() + lunar.getDayPengZuZhi()
        pengzu = "、".join(pengzu_list) if pengzu_list else ""
    except Exception:
        pengzu = ""
    try:
        dir_xi     = lunar.getDayPositionXiDesc()
        dir_fu     = lunar.getDayPositionFuDesc()
        dir_cai    = lunar.getDayPositionCaiDesc()
        dir_yanggui= lunar.getDayPositionYangGuiDesc()
        dir_yingui = lunar.getDayPositionYinGuiDesc()
    except Exception:
        dir_xi = dir_fu = dir_cai = dir_yanggui = dir_yingui = ""
    return {
        "date": date_str, "weekday": weekday, "lunar_ymd": lunar_ymd,
        "year_gz": year_gz, "month_gz": month_gz, "day_gz": day_gz,
        "day_zhi": day_zhi, "day_nayin": day_nayin,
        "yi": yi, "ji": ji, "chong_desc": chong_desc, "sha": sha,
        "tianshen": tianshen, "tianshen_luck": tianshen_luck,
        "zhixing": zhixing, "xiu": xiu, "xiu_luck": xiu_luck,
        "pengzu": pengzu,
        "dir": {"xi": dir_xi, "fu": dir_fu, "cai": dir_cai, "yanggui": dir_yanggui, "yingui": dir_yingui}
    }

def build_basic_hour_table(lunar, day_gz):
    day_gan_idx = GAN.index(day_gz[0])
    start_gan_map = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8]
    start_gan_idx = start_gan_map[day_gan_idx]
    solar_day = lunar.getSolar()
    yy, mm, dd = solar_day.getYear(), solar_day.getMonth(), solar_day.getDay()
    table = []
    for i, zhi in enumerate(SHI_CHEN_LABELS):
        gan_idx = (start_gan_idx + i) % 10
        gz = GAN[gan_idx] + zhi
        chong_zhi_idx = (ZHI.index(zhi) + 6) % 12
        chong_zhi = ZHI[chong_zhi_idx]
        chong_d = f"冲{chong_zhi}"
        try:
            hh = SHI_CHEN_SAMPLE_HOUR[zhi]
            if zhi == "子":
                prev = datetime.date(yy, mm, dd) - datetime.timedelta(days=1)
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
            "zhi": zhi, "label": SHI_CHEN_NAMES[i], "range": SHI_CHEN_RANGES[zhi],
            "gz": gz, "luck": luck, "tianshen": ts,
            "chong_desc": chong_d, "sha": "", "yi": yi, "ji": ji,
        })
    return table

def calc_bazi_from_birth(birth_iso):
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
            return {"gz": gz, "gan": "", "zhi": "", "nayin": "", "wuxing": ""}
        g, z = gz[0], gz[1]
        return {"gz": gz, "gan": g, "zhi": z, "nayin": nayin_of(gz), "wuxing": wuxing_of_gan(g)}
    return {
        "mode": "birth", "birth_iso": birth_iso,
        "year":  pillar_info(eightChar.getYearGan()  + eightChar.getYearZhi()),
        "month": pillar_info(eightChar.getMonthGan() + eightChar.getMonthZhi()),
        "day":   pillar_info(eightChar.getDayGan()   + eightChar.getDayZhi()),
        "time":  pillar_info(eightChar.getTimeGan()  + eightChar.getTimeZhi()),
    }

def build_bazi_manual(year_gz, month_gz, day_gz, time_gz):
    def pillar_info(gz):
        if not gz or len(gz) < 2:
            return {"gz": gz, "gan": "", "zhi": "", "nayin": None, "wuxing": None}
        return {"gz": gz, "gan": gz[0], "zhi": gz[1], "nayin": None, "wuxing": None}
    return {
        "mode": "manual",
        "year": pillar_info(year_gz), "month": pillar_info(month_gz),
        "day":  pillar_info(day_gz),  "time":  pillar_info(time_gz),
    }

def build_personal(day_data, bazi):
    day_master = bazi["day"]["gan"]
    user_zhis = [bazi["year"]["zhi"], bazi["month"]["zhi"], bazi["day"]["zhi"], bazi["time"]["zhi"]]
    user_zhi_labels = ["年支","月支","日支","时支"]
    user_gans = [bazi["year"]["gan"], bazi["month"]["gan"], bazi["day"]["gan"], bazi["time"]["gan"]]
    user_gan_labels = ["年干","月干","日干","时干"]
    flow_levels = [("流年", day_data["year_gz"]), ("流月", day_data["month_gz"]), ("流日", day_data["day_gz"])]
    gan_relations_list = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2: continue
        fg = level_gz[0]
        tg_shishen = ten_god(day_master, fg) if day_master else ""
        for ug, ul in zip(user_gans, user_gan_labels):
            if not ug: continue
            rels = gan_relations(fg, ug)
            for r in rels:
                gan_relations_list.append({"level": level_name, "flow_gan": fg, "user_gan": ug,
                    "user_label": ul, "rel": r, "desc": REL_DESC.get(r, ""), "ten_god": tg_shishen})
    zhi_relations_list = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2: continue
        fz = level_gz[1]
        for uz, ul in zip(user_zhis, user_zhi_labels):
            if not uz: continue
            rels = zhi_relations(fz, uz)
            if rels and rels != ["无"]:
                for r in rels:
                    zhi_relations_list.append({"level": level_name, "flow_zhi": fz, "user_zhi": uz,
                        "user_label": ul, "rel": r, "desc": REL_DESC.get(r, "")})
    cang_gan_analysis = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2: continue
        fz = level_gz[1]
        cg_list = CANG_GAN.get(fz, [])
        shishen_list = [{"gan": cg, "ten_god": ten_god(day_master, cg) if day_master else "",
            "keyword": SHISHEN_KEYWORDS.get(ten_god(day_master, cg) if day_master else "", "")} for cg in cg_list]
        cang_gan_analysis.append({"level": level_name, "flow_gz": level_gz, "flow_zhi": fz, "cang_gan": shishen_list})
    flow_ten_gods = []
    for level_name, level_gz in flow_levels:
        if not level_gz or len(level_gz) < 2: continue
        fg = level_gz[0]
        ss = ten_god(day_master, fg) if day_master else ""
        flow_ten_gods.append({"level": level_name, "flow_gz": level_gz, "flow_gan": fg,
            "ten_god": ss, "keyword": SHISHEN_KEYWORDS.get(ss, "")})
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
    # ── 个性化宜/忌 ───────────────────────────────
    # 基于命局关系 + 十神推导，替换通用黄历宜忌
    support_rels = {"合","三合","三会","同气","天干合"}
    conflict_rels = {"冲","刑","害","破","天干冲"}

    # 十神 → 宜/忌 短词映射（2-3字，与黄历格式一致）
    SHISHEN_YI = {
        "正财": ["理财","收款","签约"],
        "偏财": ["进财","开拓","投资"],
        "正官": ["公务","谒贵","立券"],
        "七杀": ["出行","竞争","求职"],
        "正印": ["学习","求医","修缮"],
        "偏印": ["研究","静修","独处"],
        "食神": ["祈福","社交","纳采"],
        "伤官": ["创作","出行","开光"],
        "比肩": ["合作","会友","立券"],
        "劫财": ["求财","动土","开市"],
    }
    SHISHEN_JI = {
        "正财": ["冲动","借贷","赌博"],
        "偏财": ["投机","冒险","散财"],
        "正官": ["违规","词讼","争执"],
        "七杀": ["动土","破土","冲煞"],
        "正印": ["嫁娶","出行","安葬"],
        "偏印": ["开市","纳财","会亲"],
        "食神": ["争执","动土","安葬"],
        "伤官": ["嫁娶","词讼","作灶"],
        "比肩": ["争执","嫁娶","借贷"],
        "劫财": ["嫁娶","安葬","开仓"],
    }
    # 地支关系 → 宜/忌 短词
    REL_YI = {"合": "合谋", "三合": "聚众", "三会": "纳财", "同气": "守成"}
    REL_JI = {"冲": "出行", "刑": "词讼", "害": "嫁娶", "破": "动土"}

    personal_yi_set = []
    personal_ji_set = []

    # 从流日地支关系提取宜忌短词
    for r in zhi_relations_list:
        if r["level"] == "流日":
            if r["rel"] in support_rels and r["rel"] in REL_YI:
                w = REL_YI[r["rel"]]
                if w not in personal_yi_set:
                    personal_yi_set.append(w)
            elif r["rel"] in conflict_rels and r["rel"] in REL_JI:
                w = REL_JI[r["rel"]]
                if w not in personal_ji_set:
                    personal_ji_set.append(w)

    # 从十神提取宜忌（取流日天干对日主的十神）
    day_flow_tg = next((t for t in flow_ten_gods if t["level"] == "流日"), None)
    if day_flow_tg and day_flow_tg["ten_god"]:
        tg = day_flow_tg["ten_god"]
        for w in SHISHEN_YI.get(tg, []):
            if w not in personal_yi_set:
                personal_yi_set.append(w)
        for w in SHISHEN_JI.get(tg, []):
            if w not in personal_ji_set:
                personal_ji_set.append(w)

    # 若完全无关系，降级到通用黄历宜忌
    if not personal_yi_set:
        personal_yi_set = list(yi_list[:6])
    if not personal_ji_set:
        personal_ji_set = list(ji_list[:4])

    return {
        "day_master": day_master,
        "gan_relations": gan_relations_list,
        "zhi_relations": zhi_relations_list,
        "cang_gan_analysis": cang_gan_analysis,
        "flow_ten_gods": flow_ten_gods,
        "summary": summary_base,
        "action_points": action_points,
        "personal_yi": personal_yi_set,
        "personal_ji": personal_ji_set,
    }

def build_personal_hour_table(basic_table, bazi):
    day_master = bazi["day"]["gan"]
    user_zhis  = [bazi["year"]["zhi"], bazi["month"]["zhi"], bazi["day"]["zhi"], bazi["time"]["zhi"]]
    user_labels= ["年支","月支","日支","时支"]

    SUPPORT_RELS  = {"合","三合","三会","同气"}
    CONFLICT_RELS = {"冲","刑","害","破"}

    # 十神对时辰的宜忌短词（2-3字）
    HOUR_TG_YI = {
        "正财":"收款", "偏财":"进财",
        "正官":"公务", "七杀":"出行",
        "正印":"学习", "偏印":"静修",
        "食神":"祈福", "伤官":"创作",
        "比肩":"合作", "劫财":"求财",
    }
    HOUR_TG_JI = {
        "正财":"借贷", "偏财":"投机",
        "正官":"词讼", "七杀":"冲煞",
        "正印":"嫁娶", "偏印":"开市",
        "食神":"争执", "伤官":"嫁娶",
        "比肩":"争执", "劫财":"安葬",
    }
    # 地支关系 → 时辰宜/忌短词
    HOUR_REL_YI = {"合": "合谋", "三合": "纳财", "三会": "聚众", "同气": "守成"}
    HOUR_REL_JI = {"冲": "出行", "刑": "词讼", "害": "嫁娶", "破": "动土"}

    result = []
    for hour in basic_table:
        gz  = hour["gz"]
        zhi = hour["zhi"]
        hg  = gz[0] if gz else ""
        tg = ten_god(day_master, hg) if (day_master and hg) else ""

        rels = []
        for uz, ul in zip(user_zhis, user_labels):
            if not uz: continue
            rs = zhi_relations(zhi, uz)
            if rs and rs != ["无"]:
                for r in rs:
                    rels.append({"with": ul, "type": r})

        # 个性化吉凶：有合→吉，有冲/刑→凶，否则跟随基础
        rel_types = {r["type"] for r in rels}
        if rel_types & SUPPORT_RELS and not (rel_types & CONFLICT_RELS):
            personal_luck = "吉"
        elif rel_types & CONFLICT_RELS:
            personal_luck = "凶"
        else:
            personal_luck = hour["luck"]  # 无个性化关系时沿用基础

        # 个性化时辰宜忌（短词）
        hour_yi = []
        hour_ji = []
        for r_type in rel_types:
            if r_type in SUPPORT_RELS and r_type in HOUR_REL_YI:
                w = HOUR_REL_YI[r_type]
                if w not in hour_yi:
                    hour_yi.append(w)
            elif r_type in CONFLICT_RELS and r_type in HOUR_REL_JI:
                w = HOUR_REL_JI[r_type]
                if w not in hour_ji:
                    hour_ji.append(w)
        if tg in HOUR_TG_YI:
            w = HOUR_TG_YI[tg]
            if w not in hour_yi:
                hour_yi.append(w)
        if tg in HOUR_TG_JI:
            w = HOUR_TG_JI[tg]
            if w not in hour_ji:
                hour_ji.append(w)
        # 无个性化宜忌时降级到基础时辰宜忌
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
