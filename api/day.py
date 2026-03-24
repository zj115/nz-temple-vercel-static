# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/day
Body: { "date": "YYYY-MM-DD" }
"""
import json
import sys
import os

# 确保可以找到 _almanac 模块
sys.path.insert(0, os.path.dirname(__file__))

from _almanac import _lunar_to_day_dict, build_basic_hour_table
from lunar_python import Solar


def handler(request):
    # 处理 CORS 预检
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }

    try:
        body = json.loads(request.body)
    except Exception:
        body = {}

    date_str = body.get('date', '')
    try:
        yy, mm, dd = [int(x) for x in date_str.split('-')]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

    day_data   = _lunar_to_day_dict(lunar)
    hour_table = build_basic_hour_table(lunar, day_data['day_gz'])

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'day': day_data, 'basic_hour_table': hour_table}, ensure_ascii=False)
    }
