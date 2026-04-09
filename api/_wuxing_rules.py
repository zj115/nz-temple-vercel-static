# -*- coding: utf-8 -*-
"""
五行颜色规则表
规则依据：日干五行 → 今日五行属性 → 推荐/辅助/避免颜色
"""

# 天干 → 五行
GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 五行 → 颜色建议
WUXING_TO_COLORS = {
    "木": {
        "main":    ["绿色", "青色"],
        "support": ["黑色", "蓝色"],
        "avoid":   ["白色", "金属色"],
    },
    "火": {
        "main":    ["红色", "紫色"],
        "support": ["绿色", "青色"],
        "avoid":   ["黑色", "蓝色"],
    },
    "土": {
        "main":    ["黄色", "咖色", "米色"],
        "support": ["红色", "紫色"],
        "avoid":   ["绿色"],
    },
    "金": {
        "main":    ["白色", "金色", "银色"],
        "support": ["黄色", "咖色"],
        "avoid":   ["红色"],
    },
    "水": {
        "main":    ["黑色", "蓝色"],
        "support": ["白色", "银色"],
        "avoid":   ["黄色", "咖色"],
    },
}

# 五行 → 英文颜色建议
WUXING_TO_COLORS_EN = {
    "木": {
        "main":    ["Green", "Teal"],
        "support": ["Black", "Blue"],
        "avoid":   ["White", "Metallic"],
    },
    "火": {
        "main":    ["Red", "Purple"],
        "support": ["Green", "Teal"],
        "avoid":   ["Black", "Blue"],
    },
    "土": {
        "main":    ["Yellow", "Brown", "Beige"],
        "support": ["Red", "Purple"],
        "avoid":   ["Green"],
    },
    "金": {
        "main":    ["White", "Gold", "Silver"],
        "support": ["Yellow", "Brown"],
        "avoid":   ["Red"],
    },
    "水": {
        "main":    ["Black", "Blue"],
        "support": ["White", "Silver"],
        "avoid":   ["Yellow", "Brown"],
    },
}

# 五行 → 名称（英文）
WUXING_EN = {"木": "Wood", "火": "Fire", "土": "Earth", "金": "Metal", "水": "Water"}

# 南半球月份→季节 / 北半球月份→季节
def get_season(month: int, hemisphere: str) -> str:
    if hemisphere == "south":
        if month in (12, 1, 2):   return "summer"
        if month in (3, 4, 5):    return "autumn"
        if month in (6, 7, 8):    return "winter"
        return "spring"
    else:
        if month in (12, 1, 2):   return "winter"
        if month in (3, 4, 5):    return "spring"
        if month in (6, 7, 8):    return "summer"
        return "autumn"

SEASON_NOTE_ZH = {
    "summer": "当前为夏季，建议选择轻薄透气的面料，颜色宜清爽。",
    "autumn": "当前为秋季，可选质感厚实的面料，颜色偏沉稳为佳。",
    "winter": "当前为冬季，建议选择保暖厚实的面料，颜色可偏深沉。",
    "spring": "当前为春季，可选清新亮丽的色系，面料以轻便为宜。",
}
SEASON_NOTE_EN = {
    "summer": "Currently summer — choose light breathable fabrics, prefer cool fresh tones.",
    "autumn": "Currently autumn — heavier fabrics work well, earthy and muted tones suit the season.",
    "winter": "Currently winter — warm fabrics recommended, deeper colours are seasonally appropriate.",
    "spring": "Currently spring — light and bright colours work well, choose easy-to-layer fabrics.",
}
