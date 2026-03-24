# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/personal_day_manual
Body: { "date": "YYYY-MM-DD", "bazi": { "year_gz": "甲子", "month_gz": "丙寅", "day_gz": "丁卯", "time_gz": "己酉" } }
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from _almanac import (
    _lunar_to_day_dict, build_basic_hour_table,
    build_bazi_manual, build_personal, build_personal_hour_table,
    GAN, ZHI
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

    date_str = body.get('date', '')
    bazi_raw = body.get('bazi', {})

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

    required_keys = ['year_gz', 'month_gz', 'day_gz', 'time_gz']
    for k in required_keys:
        gz = bazi_raw.get(k, '')
        if len(gz) != 2:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'{k} 必须是2个字（天干+地支），当前：{gz}'})
            }
        if gz[0] not in GAN:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'{k} 第一个字必须是天干，当前：{gz[0]}'})
            }
        if gz[1] not in ZHI:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': f'{k} 第二个字必须是地支，当前：{gz[1]}'})
            }

    bazi = build_bazi_manual(
        bazi_raw['year_gz'], bazi_raw['month_gz'],
        bazi_raw['day_gz'],  bazi_raw['time_gz'],
    )

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
