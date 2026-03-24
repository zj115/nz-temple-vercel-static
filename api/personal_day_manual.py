# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/personal_day_manual
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from _almanac import (
    _lunar_to_day_dict, build_basic_hour_table,
    build_bazi_manual, build_personal, build_personal_hour_table,
    GAN, ZHI
)
from lunar_python import Solar

app = Flask(__name__)

@app.route('/api/personal_day_manual', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    data = request.get_json(force=True) or {}
    date_str = data.get('date', '')
    bazi_raw = data.get('bazi', {})

    try:
        yy, mm, dd = [int(x) for x in date_str.split('-')]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        resp = jsonify({'error': f'日期解析失败: {e}'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 400

    for k in ['year_gz', 'month_gz', 'day_gz', 'time_gz']:
        gz = bazi_raw.get(k, '')
        if len(gz) != 2:
            resp = jsonify({'error': f'{k} 必须是2个字（天干+地支），当前：{gz}'})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp, 400
        if gz[0] not in GAN:
            resp = jsonify({'error': f'{k} 第一个字必须是天干，当前：{gz[0]}'})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp, 400
        if gz[1] not in ZHI:
            resp = jsonify({'error': f'{k} 第二个字必须是地支，当前：{gz[1]}'})
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp, 400

    bazi = build_bazi_manual(
        bazi_raw['year_gz'], bazi_raw['month_gz'],
        bazi_raw['day_gz'],  bazi_raw['time_gz'],
    )

    day_data    = _lunar_to_day_dict(lunar)
    basic_table = build_basic_hour_table(lunar, day_data['day_gz'])
    personal    = build_personal(day_data, bazi)
    pers_table  = build_personal_hour_table(basic_table, bazi)

    resp = jsonify({
        'bazi': bazi, 'day': day_data,
        'basic_hour_table': basic_table,
        'personal': personal,
        'personal_hour_table': pers_table,
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
