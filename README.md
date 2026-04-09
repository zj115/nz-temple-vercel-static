# 新西兰财神庙 · NZ Temple

新西兰华人财神庙官网 — 财神黄历、AI问答、法事预约、南半球本地化版本。

**技术栈：** 纯静态 HTML/CSS/JS + Supabase 后端 + Vercel Serverless Functions (Python)

---

## 页面总览

| 页面 | 文件 | 功能 |
|------|------|------|
| 主页 | `index.html` | 功德榜、今日黄历、五行穿衣建议、AI问答、南半球介绍 |
| 财神黄历 | `calendar.html` | 完整黄历（基础版/南半球/北半球/个性化），12时辰卡片，PNG下载 |
| 南半球 | `southern.html` | 南半球本地化介绍页 |
| AI财神问答 | `wealth-ai.html` | 预设问答 + 本地规则引擎 |
| 课程 | `courses.html` | 课程信息页 |
| 法事预约 | `booking.html` | 超度牌位 + 代化元宝 + 清明节活动预约 |
| 法物商城 | `shop.html` | 商城页 |
| 资料 | `profile.html` | 用户资料、八字信息管理 |
| 登录 | `login.html` | 登录 / 注册 / 重置密码 |
| 后台 | `admin.html` | 管理员后台（需 role='admin'） |

---

## 导航结构（全站统一）

顺序：**主页 → 财神黄历 → 南半球 → ai财神问答 → 课程 → 法事预约 → 法物商城 → 资料**

所有页面桌面导航 (`.navlinks`) 和侧边栏 (`.sidebar-nav`) 保持完全一致的顺序和样式，无特殊按钮。

---

## 核心功能详解

### 1. 财神黄历 (`calendar.html`)

**模式：**
- **基础版** — 北半球黄历，无需登录
- **南半球黄历** — 南半球方位校正版（财神方向镜像）
- **北半球个性化** — 输入生辰或从资料读取，生成个人八字叠加黄历
- **南半球个性化** — 同上，加南半球方位校正

**数据来源：**
- 日历数据：`POST /api/day` → 基础黄历（农历、干支、时辰、宜忌、方位）
- 个性化数据：`POST /api/personal_day_birth` 或 `POST /api/personal_day_manual`
- 八字计算：`POST /api/bazi`

**12时辰卡片：**
- 每张卡片底部有提示语（`.hour-tip`），由 `generateShichenSummary()` 生成
- 规则：凶时→谨慎提示，吉时→积极建议，平时→中性指引
- 卡片使用 `display:flex; flex-direction:column`，提示语 `margin-top:auto` 贴底对齐

**PNG下载：**
- 基础版：`drawHuangliCanvas()` 生成 Canvas，H=950px
- 个性化版：同版式，标题改为"新西兰财神庙 · {用户名}个性化黄历"
- 用户名从 Supabase `getMyProfile().full_name` 读取

**八字输入方式（个性化模式）：**
- Tab 1：输入出生日期时间（系统自动推算八字）
- Tab 2：手动输入干支（年/月/日/时）
- Tab 3：从资料页面读取（需登录，读 `member_profiles` 的 bazi 字段）

---

### 2. AI财神问答 (`wealth-ai.html`)

纯前端规则引擎，无需外部API。

**功能：**
- 13个预设问题，分3类（今日行动、财运指引、南北半球）
- 点击问题生成答案，答案根据当日黄历数据（从 `/api/day` 获取）动态组合
- 加载当日黄历：页面加载时自动调用 `/api/day`，获取宜忌/方位/时辰数据用于回答

**回答规则：**
- `hasYi(kw)` / `hasJi(kw)` — 检查当日宜忌关键词
- `dayData.tianshen_luck` — 检查天神吉凶
- 方位数据 — 插入财神/喜神/福神方位
- 时辰数据 — 找出最近吉时

---

### 3. 功德榜 (`index.html`)

- 数据来自 Supabase `merit_board` 表
- 字段：`display_name`, `merit_amount`, `sort_order`, `is_visible`
- 自动滚动动画，姓名脱敏（`maskName()`）
- 双语（中/英）切换

---

### 4. 法事预约 (`booking.html`)

**服务类型：**
- 超度牌位：$188（皈依师兄）/ $288（普通信众）
- 代化元宝：$25/袋
- 清明节活动（2026-04-05）：13:00签到 → 14:00超度 → 17:00化元宝，Zoom全程直播

**邮件通知：** Formspree（`booking.html` 第694行替换 `YOUR_FORMSPREE_FORM_ID`）

---

### 5. 用户系统

**Supabase Auth + `member_profiles` 表：**
- 登录/注册/重置密码：`login.html`
- 用户资料：`profile.html`（姓名、八字年月日时四柱）
- 管理员：`role='admin'`，访问 `admin.html`

**共用函数（`supabase.js`）：**
- `getMyProfile()` — 获取当前用户资料
- `renderNavAuthBtn()` — 登录/登出按钮状态
- `_sb` — 全局 Supabase 客户端

---

## 技术架构

### 前端
- 纯 HTML/CSS/JS，无框架
- 双语：`<span class="lang-zh">` / `<span class="lang-en">`，`data-lang` 属性控制
- 语言存储在 `localStorage('lang')`
- 主题：黑色背景 + 金色调，CSS变量 `--gold`, `--gold2`, `--text` 等

### 后端（Vercel Serverless）

| 文件 | 路由 | 功能 |
|------|------|------|
| `api/day.py` | POST `/api/day` | 基础黄历（日期→农历/干支/时辰/宜忌/方位） |
| `api/personal_day_birth.py` | POST `/api/personal_day_birth` | 个性化黄历（生辰输入） |
| `api/personal_day_manual.py` | POST `/api/personal_day_manual` | 个性化黄历（手动干支） |
| `api/bazi.py` | POST `/api/bazi` | 八字计算（生辰→四柱干支） |
| `api/_almanac.py` | 内部公共模块 | 黄历逻辑共用 |

依赖：`lunar-python>=1.3.12`（见 `requirements.txt`）

### 本地开发
```bash
cd /Users/zicongjiang/Desktop/nz-temple-vercel-static
python3 app.py   # 启动 Flask，端口 5001（5000被macOS AirPlay占用）
# 访问 http://127.0.0.1:5001/
```

---

## 数据库表（Supabase）

| 表名 | 用途 |
|------|------|
| `member_profiles` | 用户资料，role='admin' 为管理员 |
| `ritual_bookings` | 法事预约记录 |
| `yuanbao_inventory` | 元宝库存批次 |
| `site_settings` | 键值配置（邮件、银行账号等） |
| `merit_board` | 功德榜数据 |

完整建表 SQL 见 `supabase-setup.sql`

---

## 部署（Vercel）

```bash
# 1. 确认 requirements.txt 只含 lunar-python>=1.3.12
# 2. 替换 booking.html 第694行 YOUR_FORMSPREE_FORM_ID
# 3. 部署
vercel --prod
```

`app.py` 仅本地使用，不影响 Vercel 部署。

---

## Supabase 配置

```javascript
// supabase.js
const SUPABASE_URL = 'https://slditilymhrlfufmpxhr.supabase.co'
const SUPABASE_KEY = 'sb_publishable_b1rZTUmreA00TdirQ5LNmQ_LXon2lfm'
const _sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY)
```

设置管理员：
```sql
UPDATE member_profiles SET role = 'admin' WHERE id = '<user_uuid>';
```

---

## localStorage 键名

| 键 | 用途 |
|----|------|
| `lang` | 当前语言（'zh' / 'en'） |
| `nztemple_bazi_v1` | 黄历页八字缓存（mode + 数据） |
