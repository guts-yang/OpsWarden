# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于 DeepSeek + RAG + FastAPI + PostgreSQL

Python
FastAPI
SQLAlchemy
PostgreSQL
pgvector
Vue3
Vite
TailwindCSS
JWT
License

---

系统流程图

---

## 目录

- [项目简介](#项目简介)
- [快速开始（本地）](#快速开始本地无需-docker)
- [RAG 模块说明](#rag-模块说明)
- [Docker 部署](#docker-部署)
- [目录结构](#目录结构)
- [API 接口](#api-接口)
- [环境变量说明](#环境变量说明)
- [团队分工](#团队分工)
- [FAQ / 已知问题](#faq--已知问题)

---

## 项目简介

OpsWarden 是一套面向企业运维场景的 AI 数字员工系统，核心功能三条线：

- **AI 问答（RAG）**：用户提问 → 向量检索知识库 → DeepSeek 生成回答；知识库无答案时自动创建工单
- **工单系统**：工单全生命周期管理（待处理 → 处理中 → 已解决 → 已关闭），支持解决方案写回知识库
- **账号管理**：运维账号增删改查、冻结/解冻、重置密码，后台可视化管理

> "Ops" stands for Operations — the domain this system serves. 
> "Warden" means a guardian or keeper — someone who watches over,
> manages, and protects. Together, OpsWarden means a guardian of 
> operations: an AI agent that stands watch over IT workflows, 
> handles repetitive tasks, and escalates when human judgment is 
> needed.

**技术栈**


| 层次           | 技术                                  | 版本/说明                        |
| ------------ | ----------------------------------- | ---------------------------- |
| 后端框架         | FastAPI + Uvicorn                   | 0.115 / 0.30                 |
| ORM          | SQLAlchemy + psycopg3               | 2.0 / 3.1+                   |
| 认证           | JWT (python-jose + passlib)         | HS256                        |
| AI 大模型       | DeepSeek API                        | deepseek-chat                |
| 向量存储         | PostgreSQL pgvector                 | cosine 相似度，与业务数据同库           |
| Embedding 模型 | BAAI/bge-small-zh-v1.5              | sentence-transformers, 512 维 |
| 前端           | Vue 3 + Vite + Pinia + Vue Router 4 | Tailwind CSS 3               |
| 数据库          | PostgreSQL                          | 16（含 pgvector 扩展）            |
| 运行时          | Python                              | 3.11 (Anaconda)              |


---

## 快速开始（本地，无需 Docker）

### 前置要求

- Python 3.11+（**推荐 Anaconda**，因 sentence-transformers 需要完整环境）
- PostgreSQL 16（本地已运行，**含 pgvector 扩展**，见下方安装说明）
- Git

### 1. 克隆仓库

```bash
git clone https://github.com/guts-yang/OpsWarden.git
cd OpsWarden
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> **注意**：sentence-transformers 较大，首次安装需要几分钟。
> 首次启动时还会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100 MB）。

### 3. 安装 PostgreSQL 16 + pgvector（Windows）

> 已安装并启用 pgvector 的可跳过此节。

**3.1 安装 PostgreSQL 16**

前往 [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) 下载 PostgreSQL 16 安装包并安装。

**3.2 编译安装 pgvector（需要 Visual Studio Build Tools）**

pgvector 没有 Windows 预编译包，需从源码编译：

```cmd
:: 1. 下载源码：https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.2.zip
:: 2. 解压到任意目录，如 D:\pgvector-0.8.2

:: 3. 用管理员身份打开"x64 Native Tools Command Prompt for VS 2022"
:: 4. 进入源码目录（注意先切换盘符）
D:
cd D:\pgvector-0.8.2

:: 5. 设置 PostgreSQL 安装路径（按实际路径修改）
set "PGROOT=D:\PostgreSQL\16"

:: 6. 编译并安装
nmake /f Makefile.win
nmake /f Makefile.win install
```

**3.3 初始化数据库**

```bash
# 创建数据库
createdb -U postgres opswarden

# 执行初始化脚本（建表 + 插入默认管理员）
set PGCLIENTENCODING=UTF8
psql -U postgres -d opswarden -f init.sql
```

`init.sql` 会自动完成：

- 启用 `vector` 扩展（pgvector）
- 创建所有 ENUM 类型和表（`accounts`、`tickets`、`ticket_logs`、`kb_entries`）
- `kb_entries.embedding` 列存储 512 维向量，建立 IVFFlat 近似索引
- 插入默认管理员账号：用户名 `admin`，密码 `admin123`

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填写以下字段：
```


| 变量                 | 默认值                                                          | 是否必填      |
| ------------------ | ------------------------------------------------------------ | --------- |
| `DATABASE_URL`     | `postgresql+psycopg://postgres:...@localhost:5432/opswarden` | 是（按实际修改）  |
| `JWT_SECRET_KEY`   | `CHANGE_ME_USE_RANDOM_STRING`                                | 建议修改      |
| `DEEPSEEK_API_KEY` | *(空)*                                                        | AI 回答功能必填 |


### 5. 启动后端

```bash
cd backend
# 必须使用 python -m uvicorn（确保使用正确的 Python 环境）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：访问 [http://localhost:8000/health](http://localhost:8000/health)，应返回：

```json
{"status": "healthy", "database": "connected", "vector_store": "ok", "vector_docs": 100}
```

API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

### 6. 启动前端

新开一个终端，在 `frontend/` 目录执行：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 [http://localhost:5173](http://localhost:5173)，使用 `admin` / `admin123` 登录。

> **注意**：Vite 开发服务器已配置 `/api` 代理到 `http://localhost:8000`，无需手动处理 CORS。

**生产构建：**

```bash
cd frontend
npm run build
# 输出到项目根目录的 dist/ 文件夹
```

---

## RAG 模块说明

### 架构概览

```
用户提问
  │
  ▼
POST /api/chat
  │
  ├─► embed_query()        # BGE 模型将问题编码为 512 维向量
  │       ↓
  ├─► pgvector 检索         # cosine 相似度（kb_entries.embedding <=> query_vec）
  │       ↓                # score ≥ 0.4 即命中
  ├─► [命中] → DeepSeek API 生成回答  → 返回 source="kb"
  │
  └─► [未命中] → 自动创建工单          → 返回 source="fallback"
```

### 向量存储说明

知识库向量直接存储在 PostgreSQL `kb_entries` 表的 `embedding vector(512)` 列，
无需独立向量数据库。使用 pgvector IVFFlat 索引加速近似最近邻搜索。

- 新增/更新知识库条目 → 自动调用 `retriever.add_entry()` 写入 embedding
- 删除条目 → embedding 置 NULL，自动退出搜索范围
- FAQ 首次启动自动从 `knowledge_base/OpsWarden_FAQ.md` 导入

### 依赖项检查

```bash
python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
python -c "from pgvector.sqlalchemy import Vector; print('pgvector OK')"
python -c "import httpx; print('httpx OK')"
```

---

## Docker 部署

使用 Docker Compose 一键启动 PostgreSQL（含 pgvector）：

```bash
# 启动 PostgreSQL 容器（镜像内置 pgvector，无需额外安装）
docker compose up -d

# 查看状态
docker compose ps

# 停止（保留数据）
docker compose down

# 停止并清除数据（慎用）
docker compose down -v
```

> `pgvector/pgvector:pg16` 镜像已预装 pgvector 扩展，`init.sql` 会在容器首次启动时自动执行。

启动容器后按照[步骤 5–6](#5-启动后端) 启动后端和前端。

---

## 目录结构

```
OpsWarden/
├── backend/
│   ├── knowledge_base/
│   │   └── OpsWarden_FAQ.md     # 知识库原始 Markdown（启动时自动导入）
│   └── app/
│       ├── main.py              # FastAPI 入口
│       ├── config.py            # 环境变量配置
│       ├── database.py          # 数据库连接（含 pgvector 扩展初始化）
│       ├── api/
│       │   ├── auth.py          # 登录认证
│       │   ├── account.py       # 账号管理 CRUD
│       │   ├── ticket.py        # 工单管理
│       │   ├── analytics.py     # 仪表盘统计
│       │   ├── knowledge.py     # 知识库 CRUD
│       │   └── chat.py          # AI 问答入口（RAG + 工单降级）
│       ├── middleware/
│       │   ├── auth.py          # JWT 鉴权
│       │   ├── exception.py     # 统一异常处理
│       │   └── logging.py       # 请求日志
│       ├── models/
│       │   ├── account.py       # Account ORM 模型
│       │   ├── ticket.py        # Ticket / TicketLog ORM 模型
│       │   └── knowledge.py     # KBEntry ORM 模型（含 Vector(512) embedding 列）
│       ├── schemas/
│       │   ├── account.py
│       │   ├── ticket.py
│       │   └── knowledge.py
│       ├── utils/
│       │   ├── response.py      # 统一响应格式
│       │   └── security.py      # 密码哈希 / JWT 工具
│       └── rag/
│           ├── embedder.py      # Sentence-Transformers 封装
│           ├── faq_loader.py    # Markdown FAQ 解析 → PostgreSQL
│           ├── llm.py           # DeepSeek API 调用
│           └── retriever.py     # pgvector 语义检索 + CRUD
├── frontend/                    # Vue 3 + Vite SPA
│   ├── index.html               # Vite 入口
│   ├── package.json
│   ├── vite.config.js           # 代理 /api → :8000，构建输出到 dist/
│   ├── tailwind.config.js       # MD3 色板主题
│   └── src/
│       ├── main.js              # createApp + Pinia + Router
│       ├── App.vue
│       ├── api/
│       │   ├── client.js        # Axios 实例（拦截器：token 注入 + 401 自动登出）
│       │   ├── auth.js / accounts.js / tickets.js
│       │   ├── analytics.js / knowledge.js / chat.js
│       ├── stores/
│       │   └── auth.js          # Pinia auth store（持久化到 localStorage）
│       ├── router/
│       │   └── index.js         # 路由表 + beforeEach 鉴权守卫
│       ├── layouts/
│       │   └── MainLayout.vue   # Sidebar + Header + RouterView
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── DashboardView.vue
│       │   ├── AccountsView.vue
│       │   ├── TicketsView.vue
│       │   ├── AiChatView.vue
│       │   └── KnowledgeBaseView.vue
│       └── components/
│           ├── AppSidebar.vue / AppHeader.vue
│           ├── BasePagination.vue / BaseModal.vue / BaseSlidePanel.vue
├── docs/
│   ├── API_TESTING.md           # API 测试文档
│   └── backend.md               # 后端设计文档
├── init.sql                     # 数据库初始化脚本（PostgreSQL + pgvector）
├── requirements.txt             # Python 依赖
├── docker-compose.yml           # Docker 编排（PostgreSQL + pgvector）
├── .env                         # 环境变量（按 .env.example 配置）
└── README.md
```

---

## API 接口

所有接口基础路径：`http://localhost:8000`

**认证**


| 接口  | 方法   | 路径                | 认证  |
| --- | ---- | ----------------- | --- |
| 登录  | POST | `/api/auth/login` | 无   |


**账号管理**


| 接口     | 方法    | 路径                                  | 认证             |
| ------ | ----- | ----------------------------------- | -------------- |
| 当前用户信息 | GET   | `/api/accounts/me`                  | Bearer         |
| 账号列表   | GET   | `/api/accounts`                     | Bearer (admin) |
| 创建账号   | POST  | `/api/accounts`                     | Bearer (admin) |
| 更新账号   | PUT   | `/api/accounts/{id}`                | Bearer (admin) |
| 冻结账号   | PATCH | `/api/accounts/{id}/freeze`         | Bearer (admin) |
| 解冻账号   | PATCH | `/api/accounts/{id}/unfreeze`       | Bearer (admin) |
| 重置密码   | PATCH | `/api/accounts/{id}/reset-password` | Bearer (admin) |


**工单系统**


| 接口             | 方法   | 路径                          | 认证                 |
| -------------- | ---- | --------------------------- | ------------------ |
| 自动创建工单（RAG 降级） | POST | `/api/tickets/auto`         | 无                  |
| 手动创建工单         | POST | `/api/tickets/manual`       | Bearer             |
| 工单列表           | GET  | `/api/tickets`              | Bearer             |
| 工单详情           | GET  | `/api/tickets/{id}`         | Bearer             |
| 工单日志           | GET  | `/api/tickets/{id}/logs`    | Bearer             |
| 更新工单           | PUT  | `/api/tickets/{id}`         | Bearer (operator+) |
| 解决工单           | POST | `/api/tickets/{id}/resolve` | Bearer (operator+) |
| 关闭工单           | POST | `/api/tickets/{id}/close`   | Bearer (operator+) |


**知识库**


| 接口    | 方法     | 路径                     | 认证     |
| ----- | ------ | ---------------------- | ------ |
| 知识库统计 | GET    | `/api/knowledge/stats` | Bearer |
| 知识库列表 | GET    | `/api/knowledge`       | Bearer |
| 新增条目  | POST   | `/api/knowledge`       | Bearer |
| 更新条目  | PUT    | `/api/knowledge/{id}`  | Bearer |
| 删除条目  | DELETE | `/api/knowledge/{id}`  | Bearer |


**AI 问答 & 统计**


| 接口         | 方法   | 路径                       | 认证     |
| ---------- | ---- | ------------------------ | ------ |
| AI 问答（RAG） | POST | `/api/chat`              | Bearer |
| 仪表盘统计      | GET  | `/api/analytics/summary` | Bearer |


完整接口文档：[http://localhost:8000/docs](http://localhost:8000/docs)（Swagger UI）

---

## 环境变量说明

完整模板见 `.env`，以下为关键变量：


| 变量                                | 默认值                                                          | 说明                          |
| --------------------------------- | ------------------------------------------------------------ | --------------------------- |
| `DATABASE_URL`                    | `postgresql+psycopg://postgres:...@localhost:5432/opswarden` | 数据库连接串，**按实际修改**            |
| `JWT_SECRET_KEY`                  | `CHANGE_ME_USE_RANDOM_STRING`                                | JWT 签名密钥，生产环境必须修改           |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `480`                                                        | Token 有效期（分钟）               |
| `DEEPSEEK_API_KEY`                | *(空)*                                                        | DeepSeek API 密钥，**AI 回答必填** |
| `DEEPSEEK_MODEL`                  | `deepseek-chat`                                              | 使用的模型                       |
| `EMBEDDING_MODEL`                 | `BAAI/bge-small-zh-v1.5`                                     | Embedding 模型名（首次自动下载）       |
| `RAG_SCORE_THRESHOLD`             | `0.4`                                                        | 检索相似度阈值（< 此值则触发工单）          |
| `RAG_TOP_K`                       | `3`                                                          | 检索返回最大条数                    |


生成强密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 团队分工


| 成员             | 负责模块                   | 主要文件                                                    |
| -------------- | ---------------------- | ------------------------------------------------------- |
| **廖晨扬**        | AI 核心 / RAG / DeepSeek | `backend/app/rag/`                                      |
| **吴雨彤**        | 后端业务 / 账号 / 工单 / 数据库   | `backend/app/api/` · `backend/app/models/` · `init.sql` |
| **廖晨扬+Stitch** | 前端全部页面                 | `frontend/`                                             |
| **丁其彬**        | 飞书集成 / Docker / 云服务器   | `docker-compose.yml` · 飞书 Webhook                       |


---

## FAQ / 已知问题

**Q: 后端启动报 `ModuleNotFoundError: No module named 'psycopg'`？**

A: 使用了错误的 Python 环境。改用 `python -m uvicorn app.main:app` 启动，确保使用已安装依赖的 Python 环境（通常是 Anaconda）。

**Q: 后端启动报 `[WinError 10048]` 端口占用？**

A: 上次进程未正常退出。执行 `taskkill /F /IM python.exe /T` 清理后重启。

**Q: AI 回答正常但没有 DeepSeek 的生成内容？**

A: `.env` 中 `DEEPSEEK_API_KEY` 未填写。RAG 检索仍会工作，但 LLM 调用被跳过，返回知识库原始文本。

**Q: pgvector 扩展安装失败？**

A: 需要 Visual Studio Build Tools（含 C++ 工具集）。以管理员身份打开"x64 Native Tools Command Prompt for VS 2022"，并确保 `PGROOT` 指向正确的 PostgreSQL 安装目录。

**Q: `psql` 执行 init.sql 报编码错误（GBK/UTF8）？**

A: Windows 终端默认 GBK 编码与 PostgreSQL UTF8 不兼容。执行前运行：

```cmd
set PGCLIENTENCODING=UTF8
psql -U postgres -d opswarden -f init.sql
```

**Q: 健康检查返回 `vector_store: error`？**

A: pgvector 扩展未正确安装或未在数据库中启用。确认执行过 `CREATE EXTENSION IF NOT EXISTS vector;`，可在 psql 中运行 `\dx` 查看已安装扩展。

**Q: 前端 `npm run dev` 报 `Cannot find module` 错误？**

A: 先运行 `cd frontend && npm install` 安装依赖，再执行 `npm run dev`。

**Q: 浏览器显示"无法连接到后端服务"？**

A: 确认后端已在 8000 端口运行（`curl http://localhost:8000/health`）。开发环境下 Vite 已自动代理 `/api → :8000`，无需配置 CORS。

**Q: 前端页面跳转到 login 但已登录？**

A: 清除浏览器 localStorage 后重新登录（F12 → Application → Local Storage → 清空）。

---

*OpsWarden · Ver 1.0 · 课题六：运维数字员工的建设*