# -*- coding: utf-8 -*-
"""
财神日历 Flask 后端（本地开发）
依赖: flask, lunar-python, flask-cors, openai, python-dotenv
运行: python app.py
"""

import sys
import os
import datetime as dt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lunar_python import Solar

# 加载 .env（本地开发用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from _almanac import (
    compute_bazi_from_birth, compute_bazi_from_manual,
    compute_day, compute_basic_hour_table,
    build_personal_analysis,
    split_gz, SHI_CHEN_RANGES, ZHI_ORDER,
)
from _wuxing_rules import (
    GAN_WUXING, WUXING_TO_COLORS, WUXING_TO_COLORS_EN, WUXING_EN,
    get_season, SEASON_NOTE_ZH, SEASON_NOTE_EN,
)
from ai_summary import _generate_summaries
from ai_qa import _ask as _ai_ask

app = Flask(__name__, static_folder="static", template_folder=".")
CORS(app)


def zhi_of_hour(hh: int):
    idx = (hh + 1) // 2 % 12
    zhi = ZHI_ORDER[idx]
    return zhi, zhi + "时", SHI_CHEN_RANGES[zhi]


# ──────────────────────────────────────────────
# 路由
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "calendar.html")

@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/api/bazi", methods=["POST"])
def api_bazi():
    data = request.get_json(force=True) or {}
    try:
        year   = int(data['year'])
        month  = int(data['month'])
        day    = int(data['day'])
        hour   = int(data.get('hour', 0))
        minute = int(data.get('minute', 0))
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"参数缺失或格式错误: {e}"}), 400

    try:
        birth = dt.datetime(year, month, day, hour, minute, 0)
        bazi  = compute_bazi_from_birth(birth)

        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        lunar_ymd = f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"

        zhi, sc_name, sc_range = zhi_of_hour(hour)

        return jsonify({
            'year_gz':       bazi['year']['gz'],
            'month_gz':      bazi['month']['gz'],
            'day_gz':        bazi['day']['gz'],
            'hour_gz':       bazi['time']['gz'],
            'year_nayin':    bazi['year']['nayin'],
            'month_nayin':   bazi['month']['nayin'],
            'day_nayin':     bazi['day']['nayin'],
            'hour_nayin':    bazi['time']['nayin'],
            'year_wuxing':   bazi['year']['wuxing'],
            'lunar_ymd':     lunar_ymd,
            'shichen':       sc_name,
            'shichen_range': sc_range,
            'solar':         f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        })
    except Exception as e:
        return jsonify({"error": f"八字计算失败: {e}"}), 400


@app.route("/api/day", methods=["POST"])
def api_day():
    data = request.get_json(force=True) or {}
    date_str = data.get("date", "")
    try:
        date_ = dt.date.fromisoformat(date_str)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    day_data   = compute_day(date_)
    hour_table = compute_basic_hour_table(date_)
    return jsonify({"day": day_data, "basic_hour_table": hour_table})


@app.route("/api/personal_day_birth", methods=["POST"])
def api_personal_day_birth():
    data = request.get_json(force=True) or {}
    birth_s = data.get("birth", "")
    date_s  = data.get("date", "")

    if not birth_s or not date_s:
        return jsonify({"error": "Need 'birth' and 'date'"}), 400

    try:
        birth_dt = dt.datetime.fromisoformat(birth_s.replace("T", " "))
        date_    = dt.date.fromisoformat(date_s)
    except Exception as e:
        return jsonify({"error": f"日期解析失败: {e}"}), 400

    try:
        bazi = compute_bazi_from_birth(birth_dt)
    except Exception as e:
        return jsonify({"error": f"八字计算失败: {e}"}), 400

    day      = compute_day(date_)
    personal = build_personal_analysis(day, bazi)
    return jsonify({
        "bazi":                bazi,
        "day":                 day,
        "personal":            personal,
        "basic_hour_table":    personal["basic_hour_table"],
        "personal_hour_table": personal["personal_hour_table"],
        "hour_luck_chart":     personal.get("hour_luck_chart"),
    })


@app.route("/api/personal_day_manual", methods=["POST"])
def api_personal_day_manual():
    data = request.get_json(force=True) or {}
    manual = data.get("bazi") or {}
    date_s = data.get("date", "")

    if not manual or not date_s:
        return jsonify({"error": "Need 'bazi' and 'date'"}), 400

    try:
        bazi  = compute_bazi_from_manual(manual)
        date_ = dt.date.fromisoformat(date_s)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": f"参数解析失败: {e}"}), 400

    day      = compute_day(date_)
    personal = build_personal_analysis(day, bazi)
    return jsonify({
        "bazi":                bazi,
        "day":                 day,
        "personal":            personal,
        "basic_hour_table":    personal["basic_hour_table"],
        "personal_hour_table": personal["personal_hour_table"],
        "hour_luck_chart":     personal.get("hour_luck_chart"),
    })


# 为静态文件提供服务
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


# ──────────────────────────────────────────────
# 新增：五行穿衣、AI时辰总结、AI财富问答
# ──────────────────────────────────────────────

@app.route("/api/wardrobe", methods=["POST"])
def api_wardrobe():
    data      = request.get_json(force=True) or {}
    day_gz    = (data.get("day_gz") or "").strip()
    month     = int(data.get("month") or 1)
    hemi      = (data.get("hemisphere") or "south").strip().lower()

    day_gan   = day_gz[0] if day_gz else ""
    wuxing    = GAN_WUXING.get(day_gan, "土")
    colors    = WUXING_TO_COLORS.get(wuxing, WUXING_TO_COLORS["土"])
    colors_en = WUXING_TO_COLORS_EN.get(wuxing, WUXING_TO_COLORS_EN["土"])
    season    = get_season(month, hemi)

    hemi_note_zh = (
        "以上颜色建议基于传统五行日干推算，季节说明已根据南半球时令做本地化调整。黄历干支与吉凶本体不变。"
        if hemi == "south" else
        "以上颜色建议基于传统五行日干推算，季节说明依据北半球时令。黄历干支与吉凶本体不变。"
    )
    hemi_note_en = (
        "Colour suggestions are based on traditional Five Elements principles. "
        "Seasonal context has been localised for the Southern Hemisphere. "
        "The Chinese almanac and Ganzhi calculations remain unchanged."
        if hemi == "south" else
        "Colour suggestions are based on traditional Five Elements principles. "
        "Seasonal context follows Northern Hemisphere seasons."
    )

    return jsonify({
        "wuxing": wuxing, "wuxing_en": WUXING_EN.get(wuxing, wuxing),
        "main_color": colors["main"], "support_color": colors["support"], "avoid_color": colors["avoid"],
        "main_color_en": colors_en["main"], "support_color_en": colors_en["support"], "avoid_color_en": colors_en["avoid"],
        "season": season,
        "season_note_zh": SEASON_NOTE_ZH[season], "season_note_en": SEASON_NOTE_EN[season],
        "hemisphere_note_zh": hemi_note_zh, "hemisphere_note_en": hemi_note_en,
    })


@app.route("/api/ai_summary", methods=["POST"])
def api_ai_summary():
    data  = request.get_json(force=True) or {}
    hours = data.get("hours") or []
    if not hours:
        return jsonify({"items": [], "ai_unavailable": True}), 400
    items = _generate_summaries(hours)
    if not items:
        return jsonify({"items": [], "ai_unavailable": True})
    return jsonify({"items": items})


@app.route("/api/ai_qa", methods=["POST"])
def api_ai_qa():
    data           = request.get_json(force=True) or {}
    question       = (data.get("question") or "").strip()
    visible_prompt = (data.get("visible_prompt") or "").strip()
    lang           = (data.get("lang") or "zh").strip()
    if not question:
        return jsonify({"answer": "", "ai_unavailable": True}), 400
    answer = _ai_ask(question, visible_prompt, lang)
    if not answer:
        fallback = ("AI assistant is currently unavailable."
                    if lang == "en" else "AI助手暂时不可用，请直接参考今日黄历内容。")
        return jsonify({"answer": fallback, "ai_unavailable": True})
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
