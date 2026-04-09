# -*- coding: utf-8 -*-
"""
Vercel Serverless: POST /api/ai_qa
AI智能财富问答

请求体:
  {
    "question": "今天适合签约吗？",
    "visible_prompt": "今日黄历...(前端拼合的当前页面内容)",
    "lang": "zh"   // 或 "en"
  }

响应:
  { "answer": "基于今日黄历，..." }

AI不可用时返回:
  { "answer": "", "ai_unavailable": true }
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))


def _ask(question: str, visible_prompt: str, lang: str) -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.environ.get("OPENAI_API_KEY", "")
    model   = os.environ.get("OPENAI_MODEL", "claude-haiku-4-5-20251001")

    if not api_key or api_key.startswith("sk-your"):
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        return ""

    if lang == "en":
        system_prompt = """You are a wealth-oriented assistant for the "NZ Temple" Chinese almanac app.
Your role is to help users interpret their personalised almanac data in practical terms.

Rules:
1. Only use the almanac data provided in the user's context. Do not invent new fortune results.
2. Do not make absolute promises about wealth outcomes ("you will definitely make money" is forbidden).
3. If the data is insufficient to answer the question, say so clearly.
4. Answers should be practical, clear, and concise (under 150 words).
5. Tone: helpful, calm, informative — not salesy, not mystical, not over-promising.
6. You may reference specific almanac fields: Yi (auspicious), Ji (inauspicious), directions, hour luck, etc.
7. Respond in English."""
    else:
        system_prompt = """你是"新西兰财神庙"黄历App的财富向助手。
你的职责是帮助用户从个性化黄历数据中获得实用的行动参考。

规则：
1. 只使用用户提供的黄历数据作答，不允许凭空编造运势结论。
2. 不得做出绝对性财富承诺（"你一定会赚钱"等说法严禁使用）。
3. 如果数据不充分无法回答，要坦诚说明。
4. 回答要简洁有条理，不超过150字。
5. 语气：实用、平和、有条理，不要营销腔，不要神化，不要夸张。
6. 可以引用具体字段：宜/忌、财神方位、今日时运、行动建议等。
7. 用中文回答。"""

    context_content = f"""【当前黄历数据】
{visible_prompt}

【用户问题】
{question}"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": context_content},
            ],
            temperature=0.5,
            max_tokens=400,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


def handler(request):
    try:
        body = request.get_json(force=True) or {}
    except Exception:
        body = {}

    question       = (body.get("question") or "").strip()
    visible_prompt = (body.get("visible_prompt") or "").strip()
    lang           = (body.get("lang") or "zh").strip()

    if not question:
        from flask import jsonify
        return jsonify({"answer": "", "ai_unavailable": True, "error": "no question"}), 400

    answer = _ask(question, visible_prompt, lang)
    from flask import jsonify
    if not answer:
        if lang == "en":
            fallback = "AI assistant is currently unavailable. Please check your almanac data directly."
        else:
            fallback = "AI助手暂时不可用，请直接参考今日黄历内容。"
        return jsonify({"answer": fallback, "ai_unavailable": True})
    return jsonify({"answer": answer})
