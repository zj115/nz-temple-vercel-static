# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: POST /api/bazi
接收出生时间（当地时间字面值），使用参考版算法计算准确四柱八字 + 农历。

请求体 (JSON):
  { "year":1990, "month":5, "day":15, "hour":14, "minute":30, "timezone":"CN" }

响应体 (JSON):
  { "year_gz":"庚午", "month_gz":"辛巳", "day_gz":"庚辰", "hour_gz":"癸未",
    "lunar_ymd":"一九九〇年四月廿一", "shichen":"未时", "shichen_range":"13:00–14:59",
    "solar":"1990-05-15 14:30", ... }
"""
import sys, os, json, datetime as dt
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from _almanac import compute_bazi_from_birth, split_gz, SHI_CHEN_RANGES, ZHI_ORDER
from lunar_python import Solar


def zhi_of_hour(hh: int):
    """根据小时（0-23）返回时辰地支、名称和时间段。"""
    # 子时: 23:00-00:59 → hour 23 or 0
    idx = (hh + 1) // 2 % 12
    zhi = ZHI_ORDER[idx]
    return zhi, zhi + "时", SHI_CHEN_RANGES[zhi]


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

        try:
            year   = int(body['year'])
            month  = int(body['month'])
            day    = int(body['day'])
            hour   = int(body.get('hour', 0))
            minute = int(body.get('minute', 0))
        except (KeyError, ValueError, TypeError) as e:
            self._json({'error': f'参数缺失或格式错误: {e}'}, 400)
            return

        try:
            birth = dt.datetime(year, month, day, hour, minute, 0)
            bazi  = compute_bazi_from_birth(birth)

            # 农历信息
            solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
            lunar = solar.getLunar()
            lunar_ymd = f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"

            zhi, sc_name, sc_range = zhi_of_hour(hour)

            self._json({
                'year_gz':       bazi['year']['gz'],
                'month_gz':      bazi['month']['gz'],
                'day_gz':        bazi['day']['gz'],
                'hour_gz':       bazi['time']['gz'],
                'year_nayin':    bazi['year']['nayin'],
                'month_nayin':   bazi['month']['nayin'],
                'day_nayin':     bazi['day']['nayin'],
                'hour_nayin':    bazi['time']['nayin'],
                'year_wuxing':   bazi['year']['wuxing'],
                'lunar_ymd':     lunar_ymd,
                'shichen':       sc_name,
                'shichen_range': sc_range,
                'solar':         f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            })
        except Exception as e:
            self._json({'error': f'八字计算失败: {e}'}, 400)

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
