# -*- coding: utf-8 -*-
"""
Vercel Serverless: POST /api/ai_summary
批量生成12个时辰的AI白话短总结

请求体:
  {
    "hours": [
      {
        "zhi": "子", "label": "子时", "range": "23:00-00:59",
        "gz": "甲子", "luck": "吉", "tianshen": "...",
        "yi": [...], "ji": [...],
        "personal": {
          "luck": "吉", "ten_god": "正财",
          "relations": [{"with":"日支","type":"合"}],
          "yi": [...], "ji": [...]
        }
      },
      ...  (12条)
    ]
  }

响应:
  {
    "items": [
      { "zhi": "子", "ai_summary": "可进行合作洽谈，忌冒进签约。" },
      ...
    ]
  }

AI不可用时返回:
  { "items": [], "ai_unavailable": true }
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

def _build_hour_text(h: dict) -> str:
    """把单个时辰的结构化数据压缩成给AI的简短描述"""
    p = h.get("personal") or {}
    luck = p.get("luck") or h.get("luck", "")
    ten_god = p.get("ten_god") or ""
    rels = p.get("relations") or []
    rel_str = "、".join(set(r["type"] for r in rels)) if rels else "无特殊关系"
    yi = (p.get("yi") or h.get("yi") or [])[:3]
    ji = (p.get("ji") or h.get("ji") or [])[:3]
    yi_str = "、".join(yi) if yi else "无"
    ji_str = "、".join(ji) if ji else "无"
    parts = [
        f"{h['label']}（{h['range']}）",
        f"吉凶：{luck}",
    ]
    if ten_god:
        parts.append(f"十神：{ten_god}")
    parts.append(f"与命局关系：{rel_str}")
    parts.append(f"宜：{yi_str}")
    parts.append(f"忌：{ji_str}")
    return "；".join(parts)


def _generate_summaries(hours: list) -> list:
    """调用OpenAI批量生成12条总结"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001")

    if not api_key or api_key.startswith("sk-your"):
        return []

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        return []

    # 构建批量输入
    hour_lines = []
    for i, h in enumerate(hours, 1):
        hour_lines.append(f"{i}. {_build_hour_text(h)}")
    user_content = "\n".join(hour_lines)

    system_prompt = """你是"新西兰财神庙"个性化黄历的时辰总结助手。
你的任务是：把每个时辰的结构化数据转换成一句白话短总结。

规则：
1. 每条总结必须是一句话，约15-30个汉字
2. 优先使用"可/宜/忌/慎/适合/不宜/建议"等传统黄历表达
3. 不允许凭空编造未在输入中出现的运势判断
4. 只做"翻译式总结"，不是"重新算命"
5. 语气简洁直接，有轻微传统语感但容易理解
6. 如果吉凶为"凶"，语气要有明确提醒
7. 不要重复时辰名称和时间范围

必须返回严格JSON，格式如下（不要有多余文字）：
{"items":[{"zhi":"子","ai_summary":"一句话总结"},{"zhi":"丑","ai_summary":"一句话总结"}]}"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        return data.get("items", [])
    except Exception:
        return []


def handler(request):
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    hours = body.get("hours") or []
    if not hours or not isinstance(hours, list):
        from flask import jsonify
        return jsonify({"items": [], "ai_unavailable": True, "error": "no hours provided"}), 400

    items = _generate_summaries(hours)
    from flask import jsonify
    if not items:
        return jsonify({"items": [], "ai_unavailable": True})
    return jsonify({"items": items})
