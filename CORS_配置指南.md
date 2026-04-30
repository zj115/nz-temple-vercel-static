# AWS S3 CORS 配置指南

## 快速配置（推荐）

### 方法 1: AWS Console（最简单，2分钟）

1. 打开 AWS S3 Console: https://s3.console.aws.amazon.com/s3/buckets/nz-temple-media-nz?region=ap-southeast-2&tab=permissions
2. 点击 **Permissions** 标签
3. 滚动到 **Cross-origin resource sharing (CORS)** 部分
4. 点击 **Edit** 按钮
5. 粘贴以下 JSON（替换所有内容）：

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

6. 点击 **Save changes**
7. 完成！刷新视频页面即可播放

---

## 方法 2: AWS CLI（需要先配置凭证）

### 步骤 1: 配置 AWS 凭证

```bash
aws configure
```

输入：
- AWS Access Key ID: `你的 Access Key`
- AWS Secret Access Key: `你的 Secret Key`
- Default region name: `ap-southeast-2`
- Default output format: `json`

### 步骤 2: 运行配置脚本

```bash
cd /Users/zicongjiang/Desktop/nz-temple-vercel-static
./configure-s3-cors.sh
```

---

## 验证 CORS 配置

配置完成后，在浏览器控制台运行：

```javascript
fetch('https://nz-temple-media-nz.s3.amazonaws.com/fengshui/玄空风水1.mp4', {
  method: 'HEAD'
}).then(r => console.log('✅ CORS 配置成功:', r.status))
  .catch(e => console.error('❌ CORS 仍然失败:', e));
```

---

## 当前问题总结

✅ **文件名映射已修复** - 所有29个视频文件名已对齐
✅ **视频文件已上传** - S3 中所有文件都存在
❌ **CORS 未配置** - 这是唯一剩余的问题

配置 CORS 后，所有功能将正常工作：
- ✅ 视频播放
- ✅ 视频缩略图生成
- ✅ 移动端播放
