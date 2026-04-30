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

def handler(request, response):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }

    # Handle preflight
    if request.method == 'OPTIONS':
        response.status_code = 200
        response.headers.update(headers)
        return ''

    if request.method != 'POST':
        response.status_code = 405
        response.headers.update(headers)
        return json.dumps({'error': 'Method not allowed'})

    try:
        # Parse request body
        body = json.loads(request.body.decode('utf-8'))
        video_file = body.get('video_file', '').strip()

        if not video_file:
            response.status_code = 400
            response.headers.update(headers)
            return json.dumps({'error': 'video_file is required'})

        # TODO: 验证 Supabase JWT token（从 Authorization header）
        # auth_header = request.headers.get('Authorization', '')
        # if not auth_header.startswith('Bearer '):
        #     response.status_code = 401
        #     response.headers.update(headers)
        #     return json.dumps({'error': 'Unauthorized'})
        # token = auth_header[7:]
        # 用 Supabase JWT secret 验证 token...

        # Get AWS credentials from environment
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'ap-southeast-2')

        if not aws_access_key or not aws_secret_key:
            response.status_code = 500
            response.headers.update(headers)
            return json.dumps({'error': 'AWS credentials not configured'})

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

        response.status_code = 200
        response.headers.update(headers)
        return json.dumps({
            'url': presigned_url,
            'expires_in': expires_in
        })

    except ClientError as e:
        response.status_code = 500
        response.headers.update(headers)
        return json.dumps({'error': f'AWS error: {str(e)}'})
    except Exception as e:
        response.status_code = 500
        response.headers.update(headers)
        return json.dumps({'error': str(e)})
