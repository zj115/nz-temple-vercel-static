# -*- coding: utf-8 -*-
"""Vercel Serverless Function: POST /api/day"""
import sys, os, json, datetime as dt
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _almanac import compute_day, compute_basic_hour_table


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
            date_ = dt.date.fromisoformat(date_str)
        except Exception as e:
            self._json({'error': str(e)}, 400)
            return

        day_data   = compute_day(date_)
        hour_table = compute_basic_hour_table(date_)
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
