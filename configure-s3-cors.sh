#!/bin/bash
# 配置 S3 CORS 策略

BUCKET_NAME="nz-temple-media-nz"
REGION="ap-southeast-2"

echo "正在配置 S3 bucket CORS 策略..."

aws s3api put-bucket-cors \
  --bucket "$BUCKET_NAME" \
  --cors-configuration file://s3-cors-policy.json \
  --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ CORS 配置成功！"
    echo ""
    echo "验证 CORS 配置："
    aws s3api get-bucket-cors --bucket "$BUCKET_NAME" --region "$REGION"
else
    echo "❌ CORS 配置失败，请检查 AWS 凭证"
    exit 1
fi
