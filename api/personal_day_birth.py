# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/personal_day_birth
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from _almanac import (
    _lunar_to_day_dict, build_basic_hour_table,
    calc_bazi_from_birth, build_personal, build_personal_hour_table
)
from lunar_python import Solar

app = Flask(__name__)

@app.route('/api/personal_day_birth', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    data = request.get_json(force=True) or {}
    date_str  = data.get('date', '')
    birth_iso = data.get('birth', '')

    try:
        yy, mm, dd = [int(x) for x in date_str.split('-')]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        resp = jsonify({'error': f'日期解析失败: {e}'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 400

    try:
        bazi = calc_bazi_from_birth(birth_iso)
    except Exception as e:
        resp = jsonify({'error': f'八字计算失败: {e}'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 400

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
