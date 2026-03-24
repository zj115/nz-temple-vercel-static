# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/day
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify
from _almanac import _lunar_to_day_dict, build_basic_hour_table
from lunar_python import Solar

app = Flask(__name__)

@app.route('/api/day', methods=['POST', 'OPTIONS'])
def handler():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp, 200

    data = request.get_json(force=True) or {}
    date_str = data.get('date', '')
    try:
        yy, mm, dd = [int(x) for x in date_str.split('-')]
        solar = Solar.fromYmd(yy, mm, dd)
        lunar = solar.getLunar()
    except Exception as e:
        resp = jsonify({'error': str(e)})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 400

    day_data   = _lunar_to_day_dict(lunar)
    hour_table = build_basic_hour_table(lunar, day_data['day_gz'])

    resp = jsonify({'day': day_data, 'basic_hour_table': hour_table})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp
