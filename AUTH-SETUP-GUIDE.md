# 风水课程 — 登录鉴权配置指南

## 🔐 工作原理

1. **用户点击课程卡片** → 前端检查是否登录（Supabase Auth）
2. **未登录** → 弹窗提示"请先登录"，点击按钮跳转到 login.html
3. **已登录** → 前端调用 `/api/get_video_url`，传递 Supabase token
4. **后端验证身份** → 用 AWS SDK 生成 S3 签名 URL（1 小时有效期）
5. **前端播放视频** → 用签名 URL 加载视频，S3 桶保持私有

---

## ⚙️ Vercel 环境变量配置（必须）

### 第 1 步：获取 AWS 凭证

1. 登录 AWS 控制台：https://console.aws.amazon.com/iam/
2. 左侧菜单点击 **Users** → 点击你的用户名（或创建新用户）
3. 点击 **Security credentials** 标签
4. 滚动到 **Access keys** 区域，点击 **Create access key**
5. 选择用途：**Application running outside AWS**
6. 复制 **Access key ID** 和 **Secret access key**（只显示一次，务必保存）

### 第 2 步：在 Vercel 配置环境变量

1. 打开 Vercel 项目：https://vercel.com/dashboard
2. 选择你的项目 `nz-temple-vercel-static`
3. 点击 **Settings** → **Environment Variables**
4. 添加以下 3 个变量：

| Key | Value | Environment |
|-----|-------|-------------|
| `AWS_ACCESS_KEY_ID` | 你的 Access Key ID | Production, Preview, Development |
| `AWS_SECRET_ACCESS_KEY` | 你的 Secret Access Key | Production, Preview, Development |
| `AWS_REGION` | `ap-southeast-2` | Production, Preview, Development |

5. 点击 **Save**

### 第 3 步：重新部署

配置完环境变量后，Vercel 会自动触发重新部署。如果没有，手动触发：
- 在 Vercel 项目页面点击 **Deployments** → 最新部署右侧的 **⋯** → **Redeploy**

---

## 🧪 测试流程

### 1. 未登录状态
1. 访问 https://nz-temple-vercel-static.vercel.app/courses.html
2. 点击任意课程卡片
3. 应该弹出"请先登录"弹窗，点击"立即登录"跳转到 login.html

### 2. 已登录状态
1. 在 login.html 登录（或注册新账号）
2. 返回 courses.html，点击任意课程卡片
3. 应该弹出视频播放器，视频正常播放

### 3. 验证签名 URL
打开浏览器开发者工具（F12）→ Network 标签：
- 应该看到一个 POST 请求到 `/api/get_video_url`
- 响应应该包含 `{"url": "https://nz-temple-media-nz.s3.amazonaws.com/fengshui/...?X-Amz-Algorithm=...", "expires_in": 3600}`
- 视频请求的 URL 应该带有 `X-Amz-Signature` 等参数

---

## 🔒 安全说明

- **S3 桶保持私有**：不需要配置 Bucket Policy 或 CORS（之前的 S3-CONFIG-GUIDE.md 可以忽略）
- **签名 URL 有效期 1 小时**：过期后需要重新获取
- **AWS 凭证只存在 Vercel 后端**：前端无法访问
- **未来扩展**：可以在 `api/get_video_url.py` 中添加付费检查逻辑（查询 Supabase 表）

---

## 🛠️ 未来扩展：付费课程

如果要实现"部分课程需要付费"：

1. **在 Supabase 创建表**：
```sql
CREATE TABLE paid_courses (
  user_id UUID REFERENCES auth.users(id),
  course_id TEXT,
  purchased_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, course_id)
);
```

2. **修改 courses.html**：
把某些课程的 `locked: false` 改成 `locked: true`

3. **修改 api/get_video_url.py**：
在生成签名 URL 前，查询 `paid_courses` 表，检查用户是否购买了该课程

---

## 📝 本地开发

如果要在本地测试（`python3 app.py`），需要：

1. 复制 `.env.example` 为 `.env`
2. 填入你的 AWS 凭证
3. 在 `app.py` 中添加 `/api/get_video_url` 路由（参考 `api/get_video_url.py` 的逻辑）

---

## ❓ 常见问题

### Q: 视频加载失败，提示"API error: 500"
A: 检查 Vercel 环境变量是否配置正确，查看 Vercel 部署日志（Functions 标签）

### Q: 视频播放一段时间后中断
A: 签名 URL 过期（1 小时），刷新页面重新获取

### Q: 如何限制某些课程只对付费用户开放？
A: 参考上面"未来扩展：付费课程"章节

### Q: 如何防止用户分享签名 URL？
A: 签名 URL 包含用户 IP 和过期时间，但无法完全防止短期内分享。如需更严格控制，可以：
  - 缩短有效期（改为 15 分钟）
  - 在后端记录每个签名 URL 的使用次数
  - 使用 CloudFront 签名 URL（支持 IP 白名单）
