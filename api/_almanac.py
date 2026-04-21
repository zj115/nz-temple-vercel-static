# -*- coding: utf-8 -*-
"""
财神日历共用逻辑 — 供 Vercel Serverless Functions 调用
算法完全基于参考版 app.py（财神日历更新版）
"""

from __future__ import annotations
import datetime as dt
from typing import Dict, List, Tuple, Optional

from lunar_python import Solar

# ── 基础数据常量 ──────────────────────────────────────────

CHONG_PAIRS = {
    ("子","午"),("午","子"),("丑","未"),("未","丑"),("寅","申"),("申","寅"),
    ("卯","酉"),("酉","卯"),("辰","戌"),("戌","辰"),("巳","亥"),("亥","巳")
}
HE_PAIRS = {
    ("子","丑"),("丑","子"),("寅","亥"),("亥","寅"),("卯","戌"),("戌","卯"),
    ("辰","酉"),("酉","辰"),("巳","申"),("申","巳"),("午","未"),("未","午")
}
SANHE_GROUPS = [
    set(["申","子","辰"]),
    set(["亥","卯","未"]),
    set(["寅","午","戌"]),
    set(["巳","酉","丑"]),
]
HAI_PAIRS = {
    ("子","未"),("未","子"),("丑","午"),("午","丑"),("寅","巳"),("巳","寅"),
    ("卯","辰"),("辰","卯"),("申","亥"),("亥","申"),("酉","戌"),("戌","酉")
}
PO_PAIRS = {
    ("子","酉"),("酉","子"),("卯","午"),("午","卯"),("辰","丑"),("丑","辰"),
    ("未","戌"),("戌","未"),("寅","亥"),("亥","寅"),("巳","申"),("申","巳")
}
XING_GROUPS = [set(["寅","巳","申"]), set(["丑","未","戌"])]
XING_PAIRS  = {("子","卯"),("卯","子")}
ZI_XING     = set(["辰","午","酉","亥"])

GAN_SET = set(list("甲乙丙丁戊己庚辛壬癸"))
ZHI_SET = set(list("子丑寅卯辰巳午未申酉戌亥"))

GAN_INFO = {
    "甲": ("木","阳"), "乙": ("木","阴"),
    "丙": ("火","阳"), "丁": ("火","阴"),
    "戊": ("土","阳"), "己": ("土","阴"),
    "庚": ("金","阳"), "辛": ("金","阴"),
    "壬": ("水","阳"), "癸": ("水","阴"),
}
CANG_GAN = {
    "子": ["癸"], "丑": ["己","癸","辛"], "寅": ["甲","丙","戊"], "卯": ["乙"],
    "辰": ["戊","乙","癸"], "巳": ["丙","庚","戊"], "午": ["丁","己"], "未": ["己","丁","乙"],
    "申": ["庚","壬","戊"], "酉": ["辛"], "戌": ["戊","辛","丁"], "亥": ["壬","甲"],
}
GAN_HE = {
    ("甲","己"):"土", ("己","甲"):"土",
    ("乙","庚"):"金", ("庚","乙"):"金",
    ("丙","辛"):"水", ("辛","丙"):"水",
    ("丁","壬"):"木", ("壬","丁"):"木",
    ("戊","癸"):"火", ("癸","戊"):"火",
}
GAN_CHONG = {
    ("甲","庚"),("庚","甲"),("乙","辛"),("辛","乙"),
    ("丙","壬"),("壬","丙"),("丁","癸"),("癸","丁"),
}
SANHUI_GROUPS = [
    (set(["寅","卯","辰"]), "木"),
    (set(["巳","午","未"]), "火"),
    (set(["申","酉","戌"]), "金"),
    (set(["亥","子","丑"]), "水"),
]

WEEKDAY_CN = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
ZHI_ORDER  = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
SHI_CHEN_RANGES = {
    "子": "00:00–00:59", "丑": "01:00–02:59", "寅": "03:00–04:59", "卯": "05:00–06:59",
    "辰": "07:00–08:59", "巳": "09:00–10:59", "午": "11:00–12:59", "未": "13:00–14:59",
    "申": "15:00–16:59", "酉": "17:00–18:59", "戌": "19:00–20:59", "亥": "21:00–22:59",
}

# ── 工具函数 ──────────────────────────────────────────────

def split_gz(gz: str) -> Tuple[str, str]:
    if not gz or len(gz) < 2:
        return "", ""
    return gz[0], gz[-1]

def validate_gz(gz: str) -> bool:
    return bool(gz) and len(gz) == 2 and gz[0] in GAN_SET and gz[1] in ZHI_SET

def is_chong(a, b): return (a, b) in CHONG_PAIRS
def is_he(a, b):    return (a, b) in HE_PAIRS
def is_hai(a, b):   return (a, b) in HAI_PAIRS
def is_po(a, b):    return (a, b) in PO_PAIRS

def is_xing(a, b):
    if (a, b) in XING_PAIRS: return True
    if a == b and a in ZI_XING: return True
    for g in XING_GROUPS:
        if a in g and b in g and a != b: return True
    return False

def sanhe_group_of(zhi):
    for g in SANHE_GROUPS:
        if zhi in g: return g
    return None

def same_sanhe(a, b):
    ga, gb = sanhe_group_of(a), sanhe_group_of(b)
    return ga is not None and gb is not None and ga == gb

def sanhui_group_of(zhi):
    for g, elem in SANHUI_GROUPS:
        if zhi in g: return g, elem
    return None

def same_sanhui(a, b):
    ga, gb = sanhui_group_of(a), sanhui_group_of(b)
    if ga and gb and ga[0] == gb[0]: return ga[1]
    return None

def gan_relation(a, b):
    if (a, b) in GAN_HE:    return "合", GAN_HE[(a, b)]
    if (a, b) in GAN_CHONG: return "冲", None
    return None

def wuxing_overcome(a_elem, b_elem):
    return (a_elem, b_elem) in {("木","土"),("土","水"),("水","火"),("火","金"),("金","木")}

def wuxing_generate(a_elem, b_elem):
    return (a_elem, b_elem) in {("木","火"),("火","土"),("土","金"),("金","水"),("水","木")}

def ten_god(day_master_gan: str, target_gan: str) -> str:
    if day_master_gan not in GAN_INFO or target_gan not in GAN_INFO:
        return ""
    dm_elem, dm_yy = GAN_INFO[day_master_gan]
    tg_elem, tg_yy = GAN_INFO[target_gan]
    same_polar = dm_yy == tg_yy
    if dm_elem == tg_elem:                        return "比肩" if same_polar else "劫财"
    if wuxing_generate(dm_elem, tg_elem):         return "食神" if same_polar else "伤官"
    if wuxing_generate(tg_elem, dm_elem):         return "偏印" if same_polar else "正印"
    if wuxing_overcome(dm_elem, tg_elem):         return "偏财" if same_polar else "正财"
    if wuxing_overcome(tg_elem, dm_elem):         return "七杀" if same_polar else "正官"
    return ""

def describe_relation(rel: str) -> str:
    mapping = {
        "冲":  "冲表示外部刺激、移动、变化与对立增强，适合预留缓冲与备选方案，不宜急推硬压。",
        "合":  "合表示牵引、协商、绑定与整合，适合沟通、对接、合作，但也要防止拖带与牵制。",
        "害":  "害偏向暗耗、误会、不对称摩擦，宜提前澄清信息，避免口舌与模糊承诺。",
        "破":  "破偏向结构性破口、节奏被打断与计划走样，关键事项应留冗余。",
        "刑":  "刑偏向规则压力、约束、内耗或情绪紧张，宜按流程办事，避免强行顶撞。",
        "三合":"三合表示聚势成局，利于整合资源、形成共识与推进联合事项。",
        "三会":"三会表示同一气势汇聚，利于顺势推进长期主线与系统性工作。",
        "同气":"同气表示同频共振，利于延续与复盘，但也要避免因惯性而迟滞。",
    }
    return mapping.get(rel, "")

# ── 核心计算：八字 ─────────────────────────────────────────

def compute_bazi_from_birth(birth: dt.datetime) -> Dict:
    """从出生时间（datetime 对象）推算四柱八字，与参考版完全一致。"""
    solar = Solar.fromYmdHms(birth.year, birth.month, birth.day, birth.hour, birth.minute, birth.second)
    lunar = solar.getLunar()
    ec = lunar.getEightChar()
    y = ec.getYear(); m = ec.getMonth(); d = ec.getDay(); t = ec.getTime()
    y_gan, y_zhi = split_gz(y)
    m_gan, m_zhi = split_gz(m)
    d_gan, d_zhi = split_gz(d)
    t_gan, t_zhi = split_gz(t)
    return {
        "mode": "birth",
        "birth_iso": birth.isoformat(sep=" "),
        "year":  {"gz": y, "gan": y_gan, "zhi": y_zhi, "nayin": ec.getYearNaYin(),  "wuxing": ec.getYearWuXing()},
        "month": {"gz": m, "gan": m_gan, "zhi": m_zhi, "nayin": ec.getMonthNaYin(), "wuxing": ec.getMonthWuXing()},
        "day":   {"gz": d, "gan": d_gan, "zhi": d_zhi, "nayin": ec.getDayNaYin(),   "wuxing": ec.getDayWuXing()},
        "time":  {"gz": t, "gan": t_gan, "zhi": t_zhi, "nayin": ec.getTimeNaYin(),  "wuxing": ec.getTimeWuXing()},
    }

def compute_bazi_from_manual(manual: Dict) -> Dict:
    """从手动输入的四柱干支计算八字结构。"""
    y = (manual.get("year_gz")  or "").strip()
    m = (manual.get("month_gz") or "").strip()
    d = (manual.get("day_gz")   or "").strip()
    t = (manual.get("time_gz")  or "").strip()
    for name, gz in [("year_gz", y), ("month_gz", m), ("day_gz", d), ("time_gz", t)]:
        if not validate_gz(gz):
            raise ValueError(f"Invalid {name}: should be 2 chars like '甲子'")
    y_gan, y_zhi = split_gz(y); m_gan, m_zhi = split_gz(m)
    d_gan, d_zhi = split_gz(d); t_gan, t_zhi = split_gz(t)
    return {
        "mode": "manual",
        "birth_iso": None,
        "year":  {"gz": y, "gan": y_gan, "zhi": y_zhi, "nayin": None, "wuxing": None},
        "month": {"gz": m, "gan": m_gan, "zhi": m_zhi, "nayin": None, "wuxing": None},
        "day":   {"gz": d, "gan": d_gan, "zhi": d_zhi, "nayin": None, "wuxing": None},
        "time":  {"gz": t, "gan": t_gan, "zhi": t_zhi, "nayin": None, "wuxing": None},
    }

# ── 核心计算：黄历日期 ─────────────────────────────────────

def compute_day(date_: dt.date) -> Dict:
    """计算指定日期的黄历数据，与参考版完全一致。"""
    solar = Solar.fromYmd(date_.year, date_.month, date_.day)
    lunar = solar.getLunar()
    day_gz = lunar.getDayInGanZhi()
    _, day_zhi = split_gz(day_gz)
    return {
        "date":          date_.isoformat(),
        "weekday":       WEEKDAY_CN[date_.weekday()],
        "lunar_ymd":     f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
        "year_gz":       lunar.getYearInGanZhi(),
        "month_gz":      lunar.getMonthInGanZhi(),
        "day_gz":        day_gz,
        "day_zhi":       day_zhi,
        "day_nayin":     lunar.getDayNaYin(),
        "yi":            list(lunar.getDayYi()),
        "ji":            list(lunar.getDayJi()),
        "chong_desc":    lunar.getDayChongDesc(),
        "sha":           lunar.getDaySha(),
        "tianshen":      lunar.getDayTianShen(),
        "tianshen_luck": lunar.getDayTianShenLuck(),
        "zhixing":       lunar.getZhiXing(),
        "xiu":           lunar.getXiu(),
        "xiu_luck":      lunar.getXiuLuck(),
        "pengzu":        f"{lunar.getPengZuGan()}；{lunar.getPengZuZhi()}",
        "dir": {
            "xi":      lunar.getPositionXiDesc(),
            "fu":      lunar.getPositionFuDesc(),
            "cai":     lunar.getPositionCaiDesc(),
            "yanggui": lunar.getPositionYangGuiDesc(),
            "yingui":  lunar.getPositionYinGuiDesc(),
        }
    }

# ── 核心计算：时辰表 ──────────────────────────────────────

def compute_basic_hour_table(date_: dt.date) -> List[Dict]:
    """生成基础12时辰表，与参考版完全一致（使用 getTimes()）。"""
    solar = Solar.fromYmd(date_.year, date_.month, date_.day)
    lunar = solar.getLunar()
    time_map = {t.getZhi(): t for t in lunar.getTimes()[:12]}
    rows = []
    for zhi in ZHI_ORDER:
        t = time_map[zhi]
        rows.append({
            "zhi":        zhi,
            "label":      zhi + "时",
            "range":      SHI_CHEN_RANGES[zhi],
            "gz":         t.getGanZhi(),
            "luck":       t.getTianShenLuck(),
            "tianshen":   t.getTianShen(),
            "chong_desc": t.getChongDesc(),
            "sha":        t.getSha(),
            "yi":         list(t.getYi()),
            "ji":         list(t.getJi()),
        })
    return rows

# ── 个性化时辰表 ──────────────────────────────────────────

# ── 时运 K 线评分 ─────────────────────────────────────────

STEM_RELATION_WEIGHTS = {"合": 4, "冲": -4, "同气": 2}
BRANCH_RELATION_WEIGHTS = {
    "三合": 8, "三会": 8, "合": 6, "同气": 4,
    "冲": -9, "刑": -7, "害": -6, "破": -5,
}
PILLAR_WEIGHTS = {
    "日支": 1.6, "日干": 1.5, "月支": 1.25, "月干": 1.15,
    "时支": 1.1, "时干": 1.0, "年支": 0.9, "年干": 0.85,
}


def _calc_component_score(weight_map: Dict, relation_type: str, pillar: str) -> int:
    base = weight_map.get(relation_type, 0)
    score = round(base * PILLAR_WEIGHTS.get(pillar, 1.0))
    if base > 0: return max(1, score)
    if base < 0: return min(-1, score)
    return 0


def _hour_base_score(row: Dict):
    reasons = []
    score = 50
    luck = row.get("luck", "")
    if "吉" in luck:
        score += 8; reasons.append({"label": f"时神{luck}", "score": 8, "kind": "support"})
    elif "凶" in luck:
        score -= 8; reasons.append({"label": f"时神{luck}", "score": -8, "kind": "risk"})
    yi_count = min(len(row.get("yi", [])), 4)
    if yi_count:
        s = yi_count * 2; score += s; reasons.append({"label": f"时宜{yi_count}项", "score": s, "kind": "support"})
    ji_terms = row.get("ji", [])
    ji_count = min(len(ji_terms), 4)
    if ji_count:
        s = -(ji_count * 3); score += s; reasons.append({"label": f"时忌{ji_count}项", "score": s, "kind": "risk"})
    if "诸事不宜" in ji_terms:
        score -= 12; reasons.append({"label": "诸事不宜强约束", "score": -12, "kind": "risk"})
    return max(0, min(100, score)), reasons


def _relation_breakdown(relations: List[Dict], layer: str) -> List[Dict]:
    weights = STEM_RELATION_WEIGHTS if layer == "stem" else BRANCH_RELATION_WEIGHTS
    items = []
    for relation in relations:
        score = _calc_component_score(weights, relation.get("type", ""), relation.get("with", ""))
        if not score: continue
        items.append({"label": f"{relation.get('type','')}{relation.get('with','')}", "score": score,
                      "kind": "support" if score > 0 else "risk", "layer": layer})
    return items


def _build_hour_luck_metrics(row: Dict, stem_relations: List[Dict], branch_relations: List[Dict]) -> Dict:
    base_score, base_reasons = _hour_base_score(row)
    stem_reasons = _relation_breakdown(stem_relations, "stem")
    branch_reasons = _relation_breakdown(branch_relations, "branch")
    all_reasons = base_reasons + stem_reasons + branch_reasons
    support_points = sum(i["score"] for i in all_reasons if i["score"] > 0)
    risk_points = sum(-i["score"] for i in all_reasons if i["score"] < 0)
    final_score = max(0, min(100, base_score + sum(i["score"] for i in stem_reasons + branch_reasons)))
    high = max(final_score, min(100, max(base_score, final_score) + round(support_points * 0.28)))
    low  = min(final_score, max(0, min(base_score, final_score) - round(risk_points * 0.24)))
    if final_score >= 75:   level = "强"
    elif final_score >= 60: level = "稳"
    elif final_score >= 45: level = "平"
    else:                   level = "谨慎"
    rationale = [
        "底分依据时神吉凶与时宜时忌数量。",
        "个性化修正依据时干与命局四干、时支与命局四支的合冲刑害破三合三会同气关系。",
        "日柱权重最高，月柱次之，时柱再次，年柱较轻。",
        "未引入喜用神强弱判断，因此这是可解释评分，不冒充完整命局断语。",
    ]
    return {
        "base_score": base_score, "score": final_score, "open": base_score, "close": final_score,
        "high": high, "low": low, "level": level,
        "support_points": support_points, "risk_points": risk_points,
        "reasons": all_reasons, "rationale": rationale,
        "support_tags": [i["label"] for i in all_reasons if i["score"] > 0][:3],
        "risk_tags":    [i["label"] for i in all_reasons if i["score"] < 0][:3],
    }


def _build_luck_chart_from_hour_table(rows: List[Dict]) -> Dict:
    items = []
    for row in rows:
        m = (row.get("personal") or {}).get("hour_luck_score") or {}
        items.append({
            "zhi": row.get("zhi"), "label": row.get("label"), "range": row.get("range"),
            "gz": row.get("gz"), "luck": row.get("luck"),
            "score": m.get("score", 50), "open": m.get("open", 50), "close": m.get("close", 50),
            "high": m.get("high", 50), "low": m.get("low", 50), "base_score": m.get("base_score", 50),
            "level": m.get("level", "平"), "support_points": m.get("support_points", 0),
            "risk_points": m.get("risk_points", 0), "support_tags": m.get("support_tags", []),
            "risk_tags": m.get("risk_tags", []), "reasons": m.get("reasons", []),
            "rationale": m.get("rationale", []),
        })
    peak   = max(items, key=lambda x: x["score"]) if items else None
    trough = min(items, key=lambda x: x["score"]) if items else None
    return {
        "model": "可解释时运评分模型",
        "description": "以时神吉凶、时宜时忌以及时柱与命局四柱的干支互动关系进行加减分，形成每个时辰的区间分与收盘分。",
        "notes": [
            "开盘分代表该时辰在未叠加个人命局前的基础时运。",
            "收盘分代表叠加个人八字关系后的个性化时运。",
            "上下影线代表该时辰的助力与风险波动区间，不是预测价格。",
        ],
        "peak_hour":   {"zhi": peak["zhi"],   "label": peak["label"],   "score": peak["score"]}   if peak   else None,
        "trough_hour": {"zhi": trough["zhi"], "label": trough["label"], "score": trough["score"]} if trough else None,
        "items": items,
    }


def build_personal_hour_table(date_: dt.date, bazi: Dict) -> List[Dict]:
    """生成个性化时辰表，与参考版完全一致。"""
    basic = compute_basic_hour_table(date_)
    day_master = split_gz(bazi["day"]["gz"])[0]
    natal_gans = [
        split_gz(bazi["year"]["gz"])[0],
        split_gz(bazi["month"]["gz"])[0],
        split_gz(bazi["day"]["gz"])[0],
        split_gz(bazi["time"]["gz"])[0],
    ]
    natal_zhis = [
        split_gz(bazi["year"]["gz"])[1],
        split_gz(bazi["month"]["gz"])[1],
        split_gz(bazi["day"]["gz"])[1],
        split_gz(bazi["time"]["gz"])[1],
    ]

    # 个性化宜/忌映射：关系类型 → 对应的活动建议
    _REL_YI = {
        "合":   ["合作洽谈", "签约对接"],
        "三合": ["整合资源", "联合推进"],
        "三会": ["顺势推进", "长期规划"],
        "同气": ["延续事务", "复盘整合"],
    }
    _REL_JI = {
        "冲":  ["冒进硬撑", "强行推动"],
        "刑":  ["违规越矩", "情绪对抗"],
        "害":  ["模糊承诺", "轻信他人"],
        "破":  ["仓促决策", "打乱节奏"],
    }

    out = []
    for row in basic:
        hg, hz = split_gz(row["gz"])
        stem_rels = []
        for pillar_label, ng in zip(["年干","月干","日干","时干"], natal_gans):
            rel = gan_relation(hg, ng)
            if rel: stem_rels.append({"with": pillar_label, "type": rel[0], "element": rel[1]})
            if hg == ng: stem_rels.append({"with": pillar_label, "type": "同气"})
        rels = []
        for pillar_label, z in zip(["年支","月支","日支","时支"], natal_zhis):
            if is_chong(hz, z):     rels.append({"with": pillar_label, "type": "冲"})
            if is_he(hz, z):        rels.append({"with": pillar_label, "type": "合"})
            if same_sanhe(hz, z):   rels.append({"with": pillar_label, "type": "三合"})
            se = same_sanhui(hz, z)
            if se:                  rels.append({"with": pillar_label, "type": "三会", "element": se})
            if is_hai(hz, z):       rels.append({"with": pillar_label, "type": "害"})
            if is_po(hz, z):        rels.append({"with": pillar_label, "type": "破"})
            if is_xing(hz, z):      rels.append({"with": pillar_label, "type": "刑"})
            if hz == z:             rels.append({"with": pillar_label, "type": "同气"})

        # 基于命局关系计算个性化吉凶
        good_types = {r["type"] for r in rels if r["type"] in ("合","三合","三会","同气")}
        bad_types  = {r["type"] for r in rels if r["type"] in ("冲","刑","害","破")}

        if good_types and not bad_types:
            p_luck = "吉"
        elif bad_types and not good_types:
            p_luck = "凶"
        elif good_types and bad_types:
            p_luck = "中"
        else:
            p_luck = row["luck"]  # 无关系则沿用基础值

        # 个性化宜：基础宜 + 命局助力对应建议
        p_yi = list(row.get("yi", []))
        for rt in good_types:
            for item in _REL_YI.get(rt, []):
                if item not in p_yi:
                    p_yi.append(item)

        # 个性化忌：基础忌 + 命局冲克对应建议
        p_ji = list(row.get("ji", []))
        for rt in bad_types:
            for item in _REL_JI.get(rt, []):
                if item not in p_ji:
                    p_ji.append(item)

        # 计算时运评分
        hour_luck_score = _build_hour_luck_metrics(row, stem_rels, rels)

        row2 = dict(row)
        row2["personal"] = {
            "ten_god":   ten_god(day_master, hg) if hg else None,
            "relations": rels,
            "luck":      p_luck,
            "yi":        p_yi,
            "ji":        p_ji,
            "hour_luck_score": hour_luck_score,
        }
        out.append(row2)
    return out

# ── 个性化分析 ────────────────────────────────────────────

def generate_daily_summary(flags: List[Dict], day: Dict) -> str:
    strong_conflict = [x for x in flags if x["type"] in ("冲","刑","害","破") and x["with"] in ("日支","日干")]
    support         = [x for x in flags if x["type"] in ("合","三合","三会","同气") and x["with"] in ("日支","日干")]
    parts = []
    if support and not strong_conflict:
        parts.append("今日与你命局之间以协同关系为主，整体节奏偏顺，适合沟通、整合资源与推进既定事项。")
    elif strong_conflict and not support:
        parts.append("今日与你命局之间以刺激性关系为主，外部变化与内在压力感较明显，重要事项宜放慢节奏并预留缓冲。")
    elif support and strong_conflict:
        parts.append("今日同时存在助力与牵制两类关系：既有可借力之处，也有容易产生摩擦或变数的环节，宜稳中求进。")
    else:
        parts.append("今日与你命局整体互动偏中性，可按既定节奏处理事务，重点在于保持稳定和执行质量。")
    yi = day.get("yi", []); ji = day.get("ji", [])
    if yi: parts.append("若结合黄历使用，优先安排\u201c" + "、".join(yi[:2]) + "\u201d类事项会更稳妥。")
    if ji: parts.append("对\u201c" + "、".join(ji[:2]) + "\u201d类事项则应更加谨慎。")
    return "".join(parts)

def build_personal_analysis(day: Dict, bazi: Dict) -> Dict:
    """生成个性化分析，与参考版 build_personal_analysis 完全一致。"""
    fy_gan, fy_zhi = split_gz(day["year_gz"])
    fm_gan, fm_zhi = split_gz(day["month_gz"])
    fd_gan, fd_zhi = split_gz(day["day_gz"])

    ny_gan, ny_zhi = split_gz(bazi["year"]["gz"])
    nm_gan, nm_zhi = split_gz(bazi["month"]["gz"])
    nd_gan, nd_zhi = split_gz(bazi["day"]["gz"])
    nt_gan, nt_zhi = split_gz(bazi["time"]["gz"])

    natal_gans  = [ny_gan, nm_gan, nd_gan, nt_gan]
    natal_zhis  = [ny_zhi, nm_zhi, nd_zhi, nt_zhi]
    day_master  = nd_gan

    def stem_checks(flow_gan, label):
        out = []
        for pillar_label, g in zip(["年干","月干","日干","时干"], natal_gans):
            rel = gan_relation(flow_gan, g)
            if rel: out.append({"with": pillar_label, "type": rel[0], "element": rel[1]})
        tg = ten_god(day_master, flow_gan) if day_master and flow_gan else None
        return {"label": label, "gan": flow_gan, "ten_god": tg, "relations": out}

    def branch_checks(flow_zhi, label):
        rels = []
        for pillar_label, z in zip(["年支","月支","日支","时支"], natal_zhis):
            if is_chong(flow_zhi, z):   rels.append({"with": pillar_label, "type": "冲"})
            if is_he(flow_zhi, z):      rels.append({"with": pillar_label, "type": "合"})
            if same_sanhe(flow_zhi, z): rels.append({"with": pillar_label, "type": "三合"})
            se = same_sanhui(flow_zhi, z)
            if se:                      rels.append({"with": pillar_label, "type": "三会", "element": se})
            if is_hai(flow_zhi, z):     rels.append({"with": pillar_label, "type": "害"})
            if is_po(flow_zhi, z):      rels.append({"with": pillar_label, "type": "破"})
            if is_xing(flow_zhi, z):    rels.append({"with": pillar_label, "type": "刑"})
            if flow_zhi == z:           rels.append({"with": pillar_label, "type": "同气"})
        hidden = [
            {"gan": hg, "ten_god": ten_god(day_master, hg)}
            for hg in CANG_GAN.get(flow_zhi, [])
            if day_master and hg
        ]
        return {"label": label, "zhi": flow_zhi, "hidden": hidden, "relations": rels}

    stem_details  = [stem_checks(fy_gan, "流年天干"), stem_checks(fm_gan, "流月天干"), stem_checks(fd_gan, "流日天干")]
    branch_details= [branch_checks(fy_zhi, "流年地支"), branch_checks(fm_zhi, "流月地支"), branch_checks(fd_zhi, "流日地支")]

    flags = []
    for part in stem_details:
        for r in part["relations"]:
            flags.append({"layer": "天干", "flow": part["label"], **r})
    for part in branch_details:
        for r in part["relations"]:
            flags.append({"layer": "地支", "flow": part["label"], **r})

    tips = []
    strong  = [x for x in flags if x.get("with") in ("日支","日干") and x.get("type") in ("冲","刑","破","害")]
    support = [x for x in flags if x.get("with") in ("日支","日干") and x.get("type") in ("合","三合","三会","同气")]
    if strong:  tips.append("重点关注：" + "；".join([f"{x['flow']}{x['layer']}{x['type']}你的{x['with']}" for x in strong]) + "。")
    if support: tips.append("可借力点：" + "；".join([f"{x['flow']}{x['layer']}{x['type']}你的{x['with']}" for x in support]) + "。")
    yi = day.get("yi", []); ji = day.get("ji", [])
    if yi: tips.append("今日宜优先考虑：" + "、".join(yi[:3]) + ("…" if len(yi) > 3 else ""))
    if ji: tips.append("今日忌需谨慎对待：" + "、".join(ji[:2]) + ("…" if len(ji) > 2 else ""))

    explanations = []
    seen = set()
    for rel in flags:
        key = (rel["flow"], rel["layer"], rel["type"], rel["with"])
        if key in seen: continue
        seen.add(key)
        explanations.append({
            "title":   f"{rel['flow']}（{rel['layer']}）{rel['type']}你的{rel['with']}",
            "meaning": describe_relation(rel["type"]),
            "note":    "这是结构关系提示，用于说明当天干支与命局之间的互动倾向，不等同于现实事件的确定性判断。"
        })

    hidden_blocks = [
        {"label": p["label"], "zhi": p["zhi"], "hidden": p["hidden"],
         "note": "藏干用于把地支内部的气分层拆开，再以日主为中心映射十神。"}
        for p in branch_details
    ]

    date_obj = dt.date.fromisoformat(day["date"])
    personal_hour_table = build_personal_hour_table(date_obj, bazi)
    hour_luck_chart = _build_luck_chart_from_hour_table(personal_hour_table)

    return {
        "summary":       generate_daily_summary(flags, day),
        "tips":          tips,
        "details": {
            "day_master": {
                "gan":     day_master,
                "wuxing":  GAN_INFO.get(day_master, (None,None))[0],
                "yinyang": GAN_INFO.get(day_master, (None,None))[1],
            },
            "flow": {
                "liunian": {"gz": day["year_gz"],  "gan": fy_gan, "zhi": fy_zhi},
                "liuyue":  {"gz": day["month_gz"], "gan": fm_gan, "zhi": fm_zhi},
                "liuri":   {"gz": day["day_gz"],   "gan": fd_gan, "zhi": fd_zhi},
            },
            "stem":   stem_details,
            "branch": branch_details,
        },
        "explanations":   explanations[:40],
        "hidden_blocks":  hidden_blocks,
        "basic_hour_table":    compute_basic_hour_table(date_obj),
        "personal_hour_table": personal_hour_table,
        "hour_luck_chart":     hour_luck_chart,
        # 兼容旧字段名（calendar.html 用到）
        "gan_relations":       [r for r in flags if r["layer"] == "天干"],
        "zhi_relations":       [r for r in flags if r["layer"] == "地支"],
        "action_points":       tips,
        "personal_yi":         yi[:6],
        "personal_ji":         ji[:4],
    }
