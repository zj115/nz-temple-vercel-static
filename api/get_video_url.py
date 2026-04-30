# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: 生成 S3 签名 URL（需登录）
POST /api/get_video_url
Body: { "video_file": "玄空风水1.mp4" }
Returns: { "url": "https://...", "expires_in": 3600 }
"""
import json
import os
import boto3
from botocore.exceptions import ClientError
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_POST(self):
        """Generate S3 presigned URL"""
        try:
            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            body = json.loads(body_bytes.decode('utf-8'))

            video_file = body.get('video_file', '').strip()
            if not video_file:
                self._send_json(400, {'error': 'video_file is required'})
                return

            # TODO: 验证 Supabase JWT token（从 Authorization header）
            # auth_header = self.headers.get('Authorization', '')
            # if not auth_header.startswith('Bearer '):
            #     self._send_json(401, {'error': 'Unauthorized'})
            #     return

            # Get AWS credentials from environment
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            aws_region = os.environ.get('AWS_REGION', 'ap-southeast-2')

            if not aws_access_key or not aws_secret_key:
                self._send_json(500, {'error': 'AWS credentials not configured'})
                return

            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )

            # Generate presigned URL (1 hour expiry)
            bucket_name = 'nz-temple-media-nz'
            object_key = f'fengshui/{video_file}'
            expires_in = 3600  # 1 hour

            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_key},
                ExpiresIn=expires_in
            )

            self._send_json(200, {
                'url': presigned_url,
                'expires_in': expires_in
            })

        except ClientError as e:
            self._send_json(500, {'error': f'AWS error: {str(e)}'})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _send_json(self, status_code, data):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

