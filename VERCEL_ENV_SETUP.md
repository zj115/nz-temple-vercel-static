# Vercel 环境变量配置说明

## AI 财神问答功能需要配置以下环境变量

### 方法 1: 通过 Vercel Dashboard（推荐）

1. 访问 https://vercel.com/zj115s-projects/nz-temple-vercel-static/settings/environment-variables
2. 添加以下环境变量：

| 变量名 | 值 | 环境 |
|--------|-----|------|
| `OPENAI_API_KEY` | 你的 OpenAI API 密钥 | Production, Preview, Development |
| `OPENAI_MODEL` | `gpt-4o-mini` | Production, Preview, Development |

3. 点击 "Save" 保存
4. 重新部署项目以使环境变量生效

### 方法 2: 通过 Vercel CLI

```bash
# 添加 OPENAI_API_KEY
vercel env add OPENAI_API_KEY production
# 粘贴你的 API 密钥

# 添加 OPENAI_MODEL
vercel env add OPENAI_MODEL production
# 输入: gpt-4o-mini

# 重新部署
vercel --prod
```

## 获取 OpenAI API 密钥

1. 访问 https://platform.openai.com/api-keys
2. 登录你的 OpenAI 账号
3. 点击 "Create new secret key"
4. 复制生成的密钥（格式：sk-proj-...）
5. 将密钥配置到 Vercel 环境变量中

## 验证配置

配置完成后，访问以下页面测试 AI 问答功能：

- 财富问答页面: https://nz-temple-vercel-static.vercel.app/wealth-ai.html
- 财神黄历页面: https://nz-temple-vercel-static.vercel.app/calendar.html

如果配置正确，AI 问答按钮应该可以正常返回结果。

## 注意事项

- ⚠️ 不要将 API 密钥提交到 Git 仓库
- ⚠️ `.env` 文件已添加到 `.gitignore`，不会被提交
- ⚠️ 本地开发时，在项目根目录创建 `.env` 文件并添加相同的环境变量
- ⚠️ OpenAI API 调用会产生费用，请注意使用量

## 当前状态

✅ 时运 K 线图功能已完全集成（无需 API 密钥）
⚠️ AI 财神问答功能需要配置有效的 OpenAI API 密钥才能使用
