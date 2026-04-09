# -*- coding: utf-8 -*-
"""
Vercel Serverless: POST /api/wardrobe
五行穿衣催财建议（规则驱动，不调用AI）

请求体:
  { "day_gz": "甲子", "month": 4, "hemisphere": "south" }

响应:
  {
    "wuxing": "木",
    "wuxing_en": "Wood",
    "main_color": ["绿色","青色"],
    "support_color": ["黑色","蓝色"],
    "avoid_color": ["白色","金属色"],
    "main_color_en": ["Green","Teal"],
    "support_color_en": ["Black","Blue"],
    "avoid_color_en": ["White","Metallic"],
    "season": "autumn",
    "season_note_zh": "...",
    "season_note_en": "...",
    "hemisphere_note_zh": "此为解释层本地化，黄历干支本体不变。",
    "hemisphere_note_en": "..."
  }
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _wuxing_rules import (
    GAN_WUXING, WUXING_TO_COLORS, WUXING_TO_COLORS_EN, WUXING_EN,
    get_season, SEASON_NOTE_ZH, SEASON_NOTE_EN,
)

def handler(request):
    if request.method == "OPTIONS":
        from http.server import BaseHTTPRequestHandler
        pass

    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    day_gz   = (body.get("day_gz") or "").strip()
    month    = int(body.get("month") or 1)
    hemi     = (body.get("hemisphere") or "south").strip().lower()

    # 拆日干
    day_gan  = day_gz[0] if day_gz else ""
    wuxing   = GAN_WUXING.get(day_gan, "土")
    colors   = WUXING_TO_COLORS.get(wuxing, WUXING_TO_COLORS["土"])
    colors_en= WUXING_TO_COLORS_EN.get(wuxing, WUXING_TO_COLORS_EN["土"])
    season   = get_season(month, hemi)

    hemi_note_zh = (
        "以上颜色建议基于传统五行日干推算，季节说明已根据南半球时令做本地化调整。"
        "黄历干支与吉凶本体不变。"
        if hemi == "south" else
        "以上颜色建议基于传统五行日干推算，季节说明依据北半球时令。黄历干支与吉凶本体不变。"
    )
    hemi_note_en = (
        "Colour suggestions are based on traditional Five Elements (Wu Xing) principles. "
        "Seasonal context has been localised for the Southern Hemisphere. "
        "The Chinese almanac and Ganzhi calculations remain unchanged."
        if hemi == "south" else
        "Colour suggestions are based on traditional Five Elements (Wu Xing) principles. "
        "Seasonal context follows Northern Hemisphere seasons. "
        "The Chinese almanac and Ganzhi calculations remain unchanged."
    )

    result = {
        "wuxing":         wuxing,
        "wuxing_en":      WUXING_EN.get(wuxing, wuxing),
        "main_color":     colors["main"],
        "support_color":  colors["support"],
        "avoid_color":    colors["avoid"],
        "main_color_en":  colors_en["main"],
        "support_color_en": colors_en["support"],
        "avoid_color_en": colors_en["avoid"],
        "season":         season,
        "season_note_zh": SEASON_NOTE_ZH[season],
        "season_note_en": SEASON_NOTE_EN[season],
        "hemisphere_note_zh": hemi_note_zh,
        "hemisphere_note_en": hemi_note_en,
    }

    from flask import jsonify
    return jsonify(result)
