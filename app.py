# -*- coding: utf-8 -*-
"""
财神日历 Flask 后端（本地开发）
依赖: flask, lunar-python, flask-cors
运行: python app.py
"""

import sys
import os
import datetime as dt
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lunar_python import Solar

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from _almanac import (
    compute_bazi_from_birth, compute_bazi_from_manual,
    compute_day, compute_basic_hour_table,
    build_personal_analysis,
    split_gz, SHI_CHEN_RANGES, ZHI_ORDER,
)

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
    })


# 为静态文件提供服务
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
