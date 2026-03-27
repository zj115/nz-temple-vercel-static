# -*- coding: utf-8 -*-
"""Vercel Serverless Function: POST /api/personal_day_birth"""
import sys, os, json, datetime as dt
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _almanac import compute_bazi_from_birth, compute_day, build_personal_analysis


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

        birth_s = body.get('birth', '')
        date_s  = body.get('date', '')
        if not birth_s or not date_s:
            self._json({'error': "Need 'birth' and 'date'"}, 400)
            return
        try:
            birth_dt = dt.datetime.fromisoformat(birth_s.replace("T", " "))
            date_    = dt.date.fromisoformat(date_s)
        except Exception as e:
            self._json({'error': f'日期解析失败: {e}'}, 400)
            return
        try:
            bazi     = compute_bazi_from_birth(birth_dt)
        except Exception as e:
            self._json({'error': f'八字计算失败: {e}'}, 400)
            return

        day      = compute_day(date_)
        personal = build_personal_analysis(day, bazi)
        self._json({'bazi': bazi, 'day': day, 'personal': personal,
                    'basic_hour_table':    personal['basic_hour_table'],
                    'personal_hour_table': personal['personal_hour_table']})

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
