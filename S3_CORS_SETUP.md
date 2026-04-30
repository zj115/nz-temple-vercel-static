# S3 CORS 配置说明

## 问题
视频播放时出现 CORS 错误：
```
Access to video at 'https://nz-temple-media-nz.s3.amazonaws.com/fengshui/...' 
from origin 'https://nz-temple-vercel-static.vercel.app' has been blocked by CORS policy
```

## 解决方案

### 方法 1: AWS Console（推荐）

1. 登录 AWS Console: https://console.aws.amazon.com/s3/
2. 找到 bucket: `nz-temple-media-nz`
3. 点击 **Permissions** 标签
4. 滚动到 **Cross-origin resource sharing (CORS)** 部分
5. 点击 **Edit**
6. 粘贴以下 JSON 配置：

```json
[
  {
    "AllowedOrigins": [
      "https://nz-temple-vercel-static.vercel.app",
      "https://*.vercel.app",
      "http://localhost:5001",
      "http://127.0.0.1:5001"
    ],
    "AllowedMethods": [
      "GET",
      "HEAD"
    ],
    "AllowedHeaders": [
      "*"
    ],
    "ExposeHeaders": [
      "Content-Length",
      "Content-Type",
      "Content-Range",
      "Accept-Ranges"
    ],
    "MaxAgeSeconds": 3600
  }
]
```

7. 点击 **Save changes**

### 方法 2: AWS CLI

如果已配置 AWS CLI，运行：

```bash
aws s3api put-bucket-cors \
  --bucket nz-temple-media-nz \
  --cors-configuration file://s3-cors-policy.json \
  --region ap-southeast-2
```

## 验证

配置完成后，在浏览器控制台运行：

```javascript
fetch('https://nz-temple-media-nz.s3.amazonaws.com/fengshui/玄空风水1.mp4', {
  method: 'HEAD'
}).then(r => console.log('CORS OK:', r.status))
  .catch(e => console.error('CORS Failed:', e));
```

## 注意事项

1. **404 错误**: 部分视频文件不存在（玄空风水4-11, 14, 17-19, 21-29.mp4）
   - 只有这些文件存在: 1, 2, 3, 12, 13, 15, 16, 20
   - 需要上传缺失的视频文件到 S3

2. **文件命名**: 确保 S3 中的文件名与代码中的 `video_file` 完全匹配
   - 路径: `s3://nz-temple-media-nz/fengshui/玄空风水{N}.mp4`

3. **Bucket 权限**: 确保 bucket 不是完全公开的，使用 presigned URL 更安全
