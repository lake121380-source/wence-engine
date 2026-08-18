# 文策引擎 (Wence Engine)

面向短视频运营团队的一站式内容生产系统：**抓取对标博主 → AI 分析风格与爆款 → 沉淀行业知识与运营观点 → 生成可直接发布的短视频文案**。

多租户 SaaS 架构，支持订阅付费、OAuth 登录、飞书同步。

---

## ✨ 功能特性

### 1. 博主情报（Creators）
- 抓取抖音 / 小红书 / 视频号博主及其视频数据（基于 TikHub API）
- 采集播放、点赞、评论、收藏、转发等指标，自动计算「赞/播、评/播、藏/播」三互动比
- AI 四维度情报卡：账号定位、视频风格、常用话题、评论区痛点挖掘
- 支持关键词自动发现博主并批量抓取

### 2. 爆款选题（Topics）
- 关键词搜索全网爆款视频，保存为选题库
- 选题状态流转：待评审 → 已采纳 → 已使用 → 已忽略
- 一键同步到飞书多维表格

### 3. 风格模板（Style Templates）
- AI 分析单博主风格，提炼可复用的「语气 / 结构 / 钩子 / CTA / 内容公式」模板
- 支持多博主联合分析，生成融合风格

### 4. 产品资料库（Documents）
- 上传 PDF / DOCX / TXT / 图片，自动提取文本并向量化（ChromaDB）
- 文件夹分类管理

### 5. 运营观点库（Viewpoints）
- 沉淀运营者的行业立场、价值观、差异化角度，供文案生成时注入

### 6. 爆款分析（Viral Analysis）
- 三互动比量化诊断 + AI 解析「为什么爆」，输出共鸣点 / 讨论钩子 / 干货价值

### 7. 文案生成（Generate）
- **五源 RAG**：博主风格 + 行业知识 + 产品资料 + 运营观点 + 爆款洞察
- 多平台适配：抖音（口播）、小红书（图文种草）、视频号（深度观点）
- 流式输出（SSE）、多轮迭代对话、生成历史与评分

### 8. SaaS 多租户 & 认证
- 邮箱注册 / 登录、Google OAuth、GitHub OAuth、微信公众号扫码登录
- JWT 鉴权 + 会话版本控制（单点失效）
- 租户成员管理与邀请

### 9. 订阅付费
- 基于 YunGouOS 聚合支付（微信 / 支付宝 / 一码付）
- 试用期 + 月度订阅，支付回调自动开通

### 10. 平台管理后台
- 租户管理、用户管理、订单管理、内容管理、系统设置

---

## 🏗 技术架构

| 层 | 技术栈 |
| --- | --- |
| 后端 | Python 3.11 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| 向量库 | ChromaDB（RAG 语义检索） |
| 数据库 | SQLite（开发）/ MySQL（生产） |
| LLM | DeepSeek（默认，Anthropic 兼容接口）/ Anthropic Claude |
| 用户前端 | Vue 3 · Vite · Pinia · Vue Router · Naive UI · Axios |
| 管理后台 | Vue 3 · Vite · Pinia · Naive UI |
| 语音转写 | Deepgram · ffmpeg |
| 文档解析 | PyMuPDF（PDF）· python-docx（DOCX） |
| 调度 | APScheduler（定时抓取） |
| 反向代理 | Caddy（自动 HTTPS） |
| 部署 | Docker Compose |
| 测试 | Playwright（E2E）· pytest |

---

## 📁 目录结构

```
content-studio/
├── content-studio/            # 主应用
│   ├── backend/               # FastAPI 后端
│   │   ├── main.py            # 应用入口、中间件
│   │   ├── config.py          # 配置（pydantic-settings）
│   │   ├── database.py        # SQLAlchemy 引擎 / 建表
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API 路由
│   │   ├── services/          # 业务逻辑（抓取/生成/分析/知识库）
│   │   ├── tests/             # pytest 单元测试
│   │   └── requirements.txt
│   ├── frontend/              # 用户前端（Vue 3）
│   │   └── src/{views,stores,router,api}
│   ├── admin/                 # 平台管理后台（Vue 3）
│   │   └── src/{views,router,api}
│   ├── docker-compose.yml     # 编排 backend/frontend/admin/caddy
│   └── Caddyfile              # 域名与反向代理配置
├── e2e/                       # Playwright 端到端测试
├── playwright.config.js
└── package.json               # E2E 测试依赖
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+（建议使用 pnpm）
- ffmpeg（语音转写依赖，Docker 镜像已内置）

### 1. 配置环境变量

```bash
cd content-studio/backend
cp .env.example .env
# 编辑 .env，填入真实的 API Key（见下方「环境变量说明」）
```

> 根目录也有一份 `.env` 模板，实际运行读取的是 `backend/.env`（Docker 的 `env_file` 指向它）。

### 2. 启动后端

```bash
cd content-studio/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

> 端口用 **8080**，与 Vite 开发代理配置一致。启动时自动建表并创建 `./uploads` 目录。

### 3. 启动用户前端

```bash
cd content-studio/frontend
npm install        # 或 pnpm install
npm run dev        # http://localhost:5173
```

### 4. 启动管理后台

```bash
cd content-studio/admin
npm install
npm run dev        # http://localhost:5174/admin/
```

### 5. Docker 一键部署

```bash
cd content-studio
docker compose up --build -d
```

Caddy 监听 80/443，按 `Caddyfile` 将域名路由到各服务（需提前将域名解析到服务器，并修改 `Caddyfile` 中的 `wenceai.xyz` 为你的域名）。

---

## 🔑 环境变量说明

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `TIKHUB_API_KEY` | TikHub 短视频数据抓取 Key | 空 |
| `ANTHROPIC_API_KEY` | Anthropic Claude Key（`USE_DEEPSEEK=false` 时使用） | 空 |
| `DEEPSEEK_API_KEY` | DeepSeek Key | 空 |
| `SILICONFLOW_API_KEY` | SiliconFlow Key | 空 |
| `DEEPGRAM_API_KEY` | Deepgram 语音转写 Key | 空 |
| `USE_DEEPSEEK` | 是否走 DeepSeek 接口 | `true` |
| `DEEPSEEK_BASE_URL` | DeepSeek 兼容接口地址 | `https://api.deepseek.com/anthropic` |
| `DEEPSEEK_MODEL` | 模型名 | `deepseek-chat` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./content_studio.db` |
| `CHROMA_PERSIST_DIR` | ChromaDB 向量库目录 | `./chroma_db` |
| `WECHAT_APPID` / `WECHAT_APPSECRET` / `WECHAT_TOKEN` | 公众号凭证（登录/消息） | 空 |
| `YUNGOUOS_*` | YunGouOS 聚合支付商户参数 | 空 |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth 凭证 | 空 |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth 凭证 | 空 |
| `JWT_SECRET` | JWT 签名密钥（**≥32 字符**，生产必改） | 占位值 |
| `JWT_EXPIRE_HOURS` | Token 有效期（小时） | `168` |
| `FRONTEND_URL` | 前端地址（OAuth 回调用） | `http://localhost:5173` |
| `DEBUG` | 调试模式 | `false` |

---

## 🔌 API 概览

所有接口前缀 `/api`，健康检查为 `/health`。

| 模块 | 端点 | 说明 |
| --- | --- | --- |
| 认证 | `POST /auth/register` `POST /auth/login` | 邮箱注册 / 登录 |
| 认证 | `GET /auth/google/url` `POST /auth/google/callback` | Google OAuth |
| 认证 | `GET /auth/github/url` `POST /auth/github/callback` | GitHub OAuth |
| 认证 | `GET /auth/wechat/oauth-url` `POST /auth/wechat/callback` | 微信 OAuth |
| 认证 | `POST /auth/scene/create` `GET /auth/scene/{id}/status` | 公众号扫码登录 |
| 认证 | `GET /auth/me` `POST /auth/refresh` `POST /auth/change-password` | 用户信息 / 刷新 / 改密 |
| 博主 | `GET/POST /creators` `POST /creators/{id}/crawl` | 博主管理 / 抓取 |
| 博主 | `POST /creators/{id}/analyze-style` `POST /creators/discover` | 风格分析 / 发现博主 |
| 博主 | `GET/POST /creators/{id}/intel-card` | 四维情报卡 |
| 文档 | `POST /documents/upload` `GET /documents` `POST /documents/add-text` | 上传 / 列表 / 文本 |
| 选题 | `POST /topics/search` `POST /topics/save` `GET /topics` | 搜索 / 保存 / 列表 |
| 选题 | `POST /topics/{id}/analyze` `POST /topics/batch-analyze` | 爆款分析 |
| 风格 | `GET/POST /style-templates` `POST /style-templates/analyze-combined` | 模板管理 / 融合分析 |
| 生成 | `POST /generate` `POST /generate/stream` | 文案生成（普通 / SSE 流式） |
| 生成 | `GET /generations` `PATCH /generations/{id}/rate` | 历史 / 评分 |
| 观点 | `GET/POST /viewpoints` | 运营观点库 |
| 租户 | `GET /tenant/info` `POST /tenant/invite/*` | 租户信息 / 邀请成员 |
| 支付 | `POST /payment/orders` `GET /payment/orders/{id}` | 下单 / 查询 |
| 统计 | `GET /knowledge/stats` | 知识库统计 |
| 管理 | `/admin/*` | 平台后台（租户/用户/订单/内容） |

---

## 🗃 数据模型

| 模型 | 表名 | 说明 |
| --- | --- | --- |
| `Tenant` | tenants | 租户 / 企业 |
| `User` | users | 用户（邮箱 / OAuth / 微信） |
| `Subscription` | subscriptions | 订阅（trial / monthly） |
| `PaymentOrder` | payment_orders | 支付订单 |
| `Creator` | creators | 博主档案 |
| `TenantCreator` | tenant_creators | 租户-博主订阅关系 |
| `CreatorVideo` | creator_videos | 博主视频内容 |
| `CreatorIntelCard` | creator_intel_cards | 四维情报卡 |
| `OperatorViewpoint` | operator_viewpoints | 运营观点 |
| `VideoAnalysis` | video_analyses | 爆款分析 |
| `Document` | documents | 产品资料文档 |
| `DocumentFolder` | document_folders | 资料文件夹 |
| `StyleTemplate` | style_templates | 风格模板 |
| `Generation` | generations | 文案生成记录 |
| `Topic` | topics | 爆款选题 |
| `WechatScene` | wechat_scenes | 微信带参场景二维码 |
| `AdminUser` | admin_users | 平台超级管理员 |

建表由 `init_db()` 在应用启动时通过 `Base.metadata.create_all()` 自动完成；`migrate.py` 提供历史 SQLite 库的字段/表补齐脚本。

---

## 🧪 测试

```bash
# 后端单元测试
cd content-studio/backend
pytest

# 端到端测试（Playwright）
npm install
npx playwright install
npx playwright test
```

---

## 📝 安全注意事项

- **切勿提交 `.env`**：项目已通过 `.gitignore` 排除所有 `.env`、数据库、向量库、上传文件与依赖目录。
- 生产环境务必：
  - 设置强随机 `JWT_SECRET`（≥32 字符）；
  - 将 `DATABASE_URL` 切换为 MySQL；
  - 通过 Caddy 启用 HTTPS；
  - 妥善保管 TikHub / DeepSeek / Deepgram / 支付商户密钥等第三方凭证。

---

## 📄 License

Private project. All rights reserved.
