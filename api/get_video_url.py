# -*- coding: utf-8 -*-
"""
Vercel Serverless Function: 生成 S3 签名 URL（需登录）
POST /api/get_video_url
Body: { "video_file": "玄空风水1.mp4" }
Returns: { "url": "https://...", "expires_in": 3600 }
"""
import json
import os
import sys
import traceback
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
            print("=== DEBUG START ===", file=sys.stderr)
            print(f"Method: {self.command}", file=sys.stderr)
            print(f"Headers: {dict(self.headers)}", file=sys.stderr)

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            print(f"Raw body: {body_bytes}", file=sys.stderr)

            body = json.loads(body_bytes.decode('utf-8'))
            print(f"Parsed body: {body}", file=sys.stderr)

            video_file = body.get('video_file', '').strip()
            print(f"video_file: {video_file}", file=sys.stderr)

            if not video_file:
                self._send_json(400, {'error': 'missing_video_file', 'detail': 'video_file is required'})
                return

            # Check AWS credentials
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            aws_region = os.environ.get('AWS_REGION', 'ap-southeast-2')

            print(f"AWS_ACCESS_KEY_ID exists: {bool(aws_access_key)}", file=sys.stderr)
            print(f"AWS_SECRET_ACCESS_KEY exists: {bool(aws_secret_key)}", file=sys.stderr)
            print(f"AWS_REGION: {aws_region}", file=sys.stderr)

            if not aws_access_key or not aws_secret_key:
                self._send_json(500, {
                    'error': 'missing_aws_env',
                    'detail': f'AWS_ACCESS_KEY_ID={bool(aws_access_key)}, AWS_SECRET_ACCESS_KEY={bool(aws_secret_key)}'
                })
                return

            # Import boto3 (after env check to avoid import errors)
            try:
                import boto3
                from botocore.exceptions import ClientError
                print("boto3 imported successfully", file=sys.stderr)
            except ImportError as e:
                print(f"boto3 import failed: {e}", file=sys.stderr)
                self._send_json(500, {'error': 'boto3_import_failed', 'detail': str(e)})
                return

            # Create S3 client
            bucket_name = 'nz-temple-media-nz'
            object_key = f'fengshui/{video_file}'
            expires_in = 3600

            print(f"Bucket: {bucket_name}", file=sys.stderr)
            print(f"Object key: {object_key}", file=sys.stderr)
            print(f"Expires in: {expires_in}", file=sys.stderr)

            try:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
                print("S3 client created", file=sys.stderr)
            except Exception as e:
                print(f"S3 client creation failed: {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self._send_json(500, {'error': 's3_client_failed', 'detail': str(e)})
                return

            # Generate presigned URL
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_key},
                    ExpiresIn=expires_in
                )
                print(f"Presigned URL generated: {presigned_url[:100]}...", file=sys.stderr)
                print("=== DEBUG END ===", file=sys.stderr)

                self._send_json(200, {
                    'url': presigned_url,
                    'expires_in': expires_in
                })
            except ClientError as e:
                print(f"Presign failed (ClientError): {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self._send_json(500, {'error': 'presign_failed', 'detail': str(e)})
            except Exception as e:
                print(f"Presign failed (Exception): {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                self._send_json(500, {'error': 'presign_failed', 'detail': str(e)})

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            self._send_json(400, {'error': 'invalid_json', 'detail': str(e)})
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            self._send_json(500, {'error': 'internal_error', 'detail': str(e), 'traceback': traceback.format_exc()})

    def _send_json(self, status_code, data):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response_json = json.dumps(data, ensure_ascii=False)
        print(f"Response ({status_code}): {response_json}", file=sys.stderr)
        self.wfile.write(response_json.encode('utf-8'))

