# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/day
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))

from _almanac import _lunar_to_day_dict, build_basic_hour_table
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
        try:
            yy, mm, dd = [int(x) for x in date_str.split('-')]
            solar = Solar.fromYmd(yy, mm, dd)
            lunar = solar.getLunar()
        except Exception as e:
            self._json({'error': str(e)}, 400)
            return

        day_data   = _lunar_to_day_dict(lunar)
        hour_table = build_basic_hour_table(lunar, day_data['day_gz'])
        self._json({'day': day_data, 'basic_hour_table': hour_table})

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
