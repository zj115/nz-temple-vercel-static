# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/personal_day_manual
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))

from _almanac import (
    _lunar_to_day_dict, build_basic_hour_table,
    build_bazi_manual, build_personal, build_personal_hour_table,
    GAN, ZHI
)
from lunar_python import Solar


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception:
            body = {}

        date_str = body.get('date', '')
        bazi_raw = body.get('bazi', {})

        try:
            yy, mm, dd = [int(x) for x in date_str.split('-')]
            solar = Solar.fromYmd(yy, mm, dd)
            lunar = solar.getLunar()
        except Exception as e:
            self._json({'error': f'日期解析失败: {e}'}, 400)
            return

        for k in ['year_gz', 'month_gz', 'day_gz', 'time_gz']:
            gz = bazi_raw.get(k, '')
            if len(gz) != 2:
                self._json({'error': f'{k} 必须是2个字（天干+地支），当前：{gz}'}, 400)
                return
            if gz[0] not in GAN:
                self._json({'error': f'{k} 第一个字必须是天干，当前：{gz[0]}'}, 400)
                return
            if gz[1] not in ZHI:
                self._json({'error': f'{k} 第二个字必须是地支，当前：{gz[1]}'}, 400)
                return

        bazi = build_bazi_manual(
            bazi_raw['year_gz'], bazi_raw['month_gz'],
            bazi_raw['day_gz'],  bazi_raw['time_gz'],
        )

        day_data    = _lunar_to_day_dict(lunar)
        basic_table = build_basic_hour_table(lunar, day_data['day_gz'])
        personal    = build_personal(day_data, bazi)
        pers_table  = build_personal_hour_table(basic_table, bazi)

        self._json({
            'bazi': bazi, 'day': day_data,
            'basic_hour_table': basic_table,
            'personal': personal,
            'personal_hour_table': pers_table,
        })

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass
