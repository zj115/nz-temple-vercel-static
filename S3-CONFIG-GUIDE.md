# S3 桶公开访问配置指南

## 问题
视频返回 403 Forbidden，因为 S3 桶 `nz-temple-media-nz` 默认是私有的。

## 解决方案（3 步，5 分钟完成）

### 第 1 步：关闭"阻止公开访问"
1. 打开 AWS S3 控制台：https://s3.console.aws.amazon.com/s3/buckets
2. 点击桶名 `nz-temple-media-nz`
3. 点击 **Permissions** 标签
4. 找到 **Block public access (bucket settings)**，点击右侧 **Edit**
5. **取消勾选** "Block all public access"
6. 点击 **Save changes**，在弹窗中输入 `confirm` 确认

### 第 2 步：添加桶策略（Bucket Policy）
1. 还在 **Permissions** 标签，向下滚动到 **Bucket policy**
2. 点击 **Edit**
3. 粘贴以下 JSON（直接覆盖原有内容）：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadFengShuiVideos",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nz-temple-media-nz/fengshui/*"
    }
  ]
}
```

4. 点击 **Save changes**

### 第 3 步：配置 CORS（允许网页播放器访问）
1. 还在 **Permissions** 标签，向下滚动到 **Cross-origin resource sharing (CORS)**
2. 点击 **Edit**
3. 粘贴以下 JSON：

```json
[
  {
    "AllowedOrigins": [
      "https://nz-temple-vercel-static.vercel.app",
      "http://localhost:5001",
      "http://127.0.0.1:5001"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["Content-Length", "Content-Range", "Accept-Ranges"],
    "MaxAgeSeconds": 3600
  }
]
```

4. 点击 **Save changes**

## 验证
配置完成后，在浏览器打开这个 URL 测试：
```
https://nz-temple-media-nz.s3.amazonaws.com/fengshui/玄空风水1.mp4
```

- ✅ 如果浏览器开始播放视频 → 配置成功
- ❌ 如果还是 403 → 检查第 1 步是否真的取消了"Block all public access"

## 安全说明
- 这个策略只开放 `fengshui/` 文件夹下的文件
- 桶的其他文件夹（如果有）仍然是私有的
- 只允许读取（GET），不允许上传/删除
- CORS 只允许你的域名访问，防止其他网站盗链

## 完成后
回到 https://nz-temple-vercel-static.vercel.app/courses.html 刷新页面，点击任意课程卡片，视频应该能正常播放。
