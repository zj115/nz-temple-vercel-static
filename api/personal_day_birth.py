# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/personal_day_birth
Body: { "date": "YYYY-MM-DD", "birth": "YYYY-MM-DD HH:MM" }
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from _almanac import (
    _lunar_to_day_dict, build_basic_hour_table,
    calc_bazi_from_birth, build_personal, build_personal_hour_table
)
from lunar_python import Solar


def handler(request):
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

    date_str  = body.get('date', '')
    birth_iso = body.get('birth', '')

    try:
        yy, mm, dd = [int(x) for x in date_str.split('-')]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'日期解析失败: {e}'})
        }

    try:
        bazi = calc_bazi_from_birth(birth_iso)
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': f'八字计算失败: {e}'})
        }

    day_data   = _lunar_to_day_dict(lunar)
    basic_table= build_basic_hour_table(lunar, day_data['day_gz'])
    personal   = build_personal(day_data, bazi)
    pers_table = build_personal_hour_table(basic_table, bazi)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({
            'bazi': bazi, 'day': day_data,
            'basic_hour_table': basic_table,
            'personal': personal,
            'personal_hour_table': pers_table,
        }, ensure_ascii=False)
    }
