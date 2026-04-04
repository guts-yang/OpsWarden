# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于 DeepSeek + RAG + FastAPI + MySQL

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35)
![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vue.js&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 目录

- [项目简介](#项目简介)
- [快速开始（本地）](#快速开始本地无需-docker)
- [RAG 模块启动教程](#rag-模块启动教程)
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

**技术栈**

| 层次 | 技术 | 版本/说明 |
|---|---|---|
| 后端框架 | FastAPI + Uvicorn | 0.115 / 0.30 |
| ORM | SQLAlchemy + PyMySQL | 2.0 / 1.1 |
| 认证 | JWT (python-jose + passlib) | HS256 |
| AI 大模型 | DeepSeek API | deepseek-chat |
| 向量数据库 | ChromaDB (本地持久化) | cosine 相似度 |
| Embedding 模型 | BAAI/bge-small-zh-v1.5 | sentence-transformers, 512 维 |
| 前端 | Vue 3 + Vite + Pinia + Vue Router 4 | Tailwind CSS 3 |
| 数据库 | MySQL | 8.0 |
| 运行时 | Python | 3.11 (Anaconda) |

---

## 快速开始（本地，无需 Docker）

### 前置要求

- Python 3.11+（**推荐 Anaconda**，因 chromadb / sentence-transformers 需要完整环境）
- MySQL 8.0（本地已运行）
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

> **注意**：chromadb 和 sentence-transformers 较大，首次安装需要几分钟。
> 首次启动时还会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100 MB）。

### 3. 初始化数据库

以 root 身份登录 MySQL，执行初始化脚本：

```bash
mysql -u root -p < init.sql
```

`init.sql` 会自动完成：
- 创建数据库 `opswarden`
- 创建用户 `ops`（密码 `ops123456`）并授权
- 建表：`accounts`、`tickets`、`ticket_logs`、`kb_entries`
- 插入默认管理员账号：用户名 `admin`，密码 `admin123`

> 若 MySQL 仅允许 `localhost` 连接，需手动执行：
> ```sql
> CREATE USER IF NOT EXISTS 'ops'@'localhost' IDENTIFIED BY 'ops123456';
> GRANT ALL PRIVILEGES ON opswarden.* TO 'ops'@'localhost';
> FLUSH PRIVILEGES;
> ```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填写以下字段：
```

| 变量 | 默认值 | 是否必填 |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://root:...@localhost:3306/opswarden` | 是（按实际修改） |
| `SECRET_KEY` | `ops-warden-secret-key` | 建议修改 |
| `DEEPSEEK_API_KEY` | _(空)_ | AI 回答功能必填 |

### 5. 启动后端

```bash
cd backend
# 必须使用 python -m uvicorn（确保使用正确的 Python 环境）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：访问 [http://localhost:8000/health](http://localhost:8000/health)，应返回：
```json
{"status": "healthy", "database": "connected", "chroma": "connected", "chroma_docs": 100}
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

## RAG 模块启动教程

### 架构概览

```
用户提问
  │
  ▼
POST /api/chat
  │
  ├─► embed_query()        # BGE 模型将问题编码为 512 维向量
  │       ↓
  ├─► ChromaDB 检索        # cosine 相似度，score ≥ 0.4 即命中
  │       ↓
  ├─► [命中] → DeepSeek API 生成回答  → 返回 source="kb"
  │
  └─► [未命中] → 自动创建工单          → 返回 source="fallback"
```

### 依赖项检查

RAG 模块需要以下依赖，运行前请确认：

```bash
python -c "import chromadb; print('chromadb OK')"
python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
python -c "import httpx; print('httpx OK')"
```

若任一命令报 `ModuleNotFoundError`，请重新安装：

```bash
pip install chromadb sentence-transformers httpx
```

### 冒烟测试（不启动后端）

在 `backend/` 目录下直接运行测试脚本，验证 RAG 核心链路：

```bash
cd backend
python smoke_test_rag.py
```

预期输出（全部 PASS）：

```
[1/5] ChromaDB 连接 + 文档数     ... PASS (100 docs)
[2/5] embed_query() 向量维度     ... PASS (512-dim)
[3/5] embed_document() 向量维度  ... PASS (512-dim)
[4/5] 检索命中测试               ... PASS (3/3 命中)
[5/5] 阈值过滤测试               ... PASS (2/2 过滤)
全部通过 (5/5)
```

### 为什么 RAG 现在无法运行？

目前有以下已知问题，按优先级排列：

---

#### 问题 1：登录报 `ValueError: password cannot be longer than 72 bytes`（已修复）

**根因：**
`passlib 1.7.4` + `bcrypt >= 4.0` 存在兼容性 Bug。
passlib 内部的 `detect_wrap_bug()` 函数会用一个 > 72 字节的测试密码调用 bcrypt，
而 bcrypt 4.0+ 强制限制密码不超过 72 字节，导致 `ValueError`。

无法降级 bcrypt（chromadb 1.5.5 依赖 `bcrypt>=4.0.1`）。

**修复方案（已应用）：**
在 `backend/app/main.py` 最顶部添加猴子补丁，在所有其他模块导入之前执行：

```python
# backend/app/main.py — 必须在所有 import 之前
import passlib.handlers.bcrypt as _passlib_bcrypt
_passlib_bcrypt.detect_wrap_bug = lambda ident: False
```

> **注意**：补丁必须在 `main.py` 最顶部，不能放在 `security.py`，
> 因为 `CryptContext` 初始化发生在模块加载时，必须在此之前完成补丁。

---

#### 问题 2：`ModuleNotFoundError: No module named 'chromadb'`

**根因：**
系统中存在多个 Python 环境（Anaconda + 系统 Python）。
直接运行 `uvicorn` 命令会调用系统 Python，该环境没有 chromadb。

**修复方案：**
```bash
# 错误方式
uvicorn app.main:app

# 正确方式（使用当前激活的 Python 环境）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

#### 问题 3：AI 回答返回 `null`（非报错，而是降级）

**根因：**
`.env` 中 `DEEPSEEK_API_KEY` 未填写。
RAG 检索正常，但 DeepSeek 调用被跳过，`llm.py` 返回 `None`，
前端会收到知识库原始文本而非 AI 生成回答。

**修复方案：**
在 `.env` 中填写：
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

从 [DeepSeek 开放平台](https://platform.deepseek.com) 获取 API Key。

---

#### 问题 4：端口 8000 已占用 `[WinError 10048]`

**根因：**
上次 uvicorn 进程未正常退出（Ctrl+C 有时不会终止子进程）。

**修复方案（Windows）：**
```bash
taskkill /F /IM python.exe /T
# 然后重新启动后端
```

---

### 完整启动流程

```bash
# Step 1: 确认依赖
cd backend
python -c "import chromadb, sentence_transformers; print('依赖 OK')"

# Step 2: 冒烟测试（可选，验证 RAG 链路）
python smoke_test_rag.py

# Step 3: 启动后端
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Step 4: 验证（新终端）
curl http://localhost:8000/health
# 期望: {"database":"connected","chroma":"connected","chroma_docs":100,...}

# Step 5: 测试 RAG（需要先登录获取 token）
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"电脑无法开机怎么办"}'
```

---

## Docker 部署

如果本地未安装 MySQL，可使用 Docker Compose 一键启动数据库服务。

> **注意**：若本机 3306 端口已被占用，请先停止本地 MySQL，或修改 `docker-compose.yml` 中的端口映射（如改为 `3307:3306`），同时更新 `.env` 中的 `DATABASE_URL`。

```bash
# 启动 MySQL 容器
docker compose up -d

# 查看状态
docker compose ps

# 停止（保留数据）
docker compose down

# 停止并清除数据（慎用）
docker compose down -v
```

启动后按照[步骤 5–6](#5-启动后端) 启动后端和前端。

---

## 目录结构

```
OpsWarden/
├── backend/
│   ├── smoke_test_rag.py        # RAG 冒烟测试（独立运行）
│   ├── chroma_db/               # ChromaDB 本地持久化数据（已内置 100 条 FAQ）
│   ├── knowledge_base/
│   │   └── OpsWarden_FAQ.md     # 知识库原始 Markdown（启动时自动导入）
│   └── app/
│       ├── main.py              # FastAPI 入口（含 passlib 兼容补丁）
│       ├── config.py            # 环境变量配置
│       ├── database.py          # 数据库连接
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
│       │   └── knowledge.py     # KBEntry ORM 模型
│       ├── schemas/
│       │   ├── account.py
│       │   ├── ticket.py
│       │   └── knowledge.py
│       ├── utils/
│       │   ├── response.py      # 统一响应格式
│       │   └── security.py      # 密码哈希 / JWT 工具
│       └── rag/
│           ├── chroma_client.py # ChromaDB 持久化客户端（LRU 缓存）
│           ├── embedder.py      # Sentence-Transformers 封装
│           ├── faq_loader.py    # Markdown FAQ 解析 → MySQL + ChromaDB
│           ├── llm.py           # DeepSeek API 调用
│           └── retriever.py     # 语义检索 + ChromaDB CRUD
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
├── init.sql                     # 数据库初始化脚本
├── requirements.txt             # Python 依赖
├── docker-compose.yml           # Docker 编排（仅 MySQL）
├── .env.example                 # 环境变量模板
└── README.md
```

---

## API 接口

所有接口基础路径：`http://localhost:8000`

**认证**

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| 登录 | POST | `/api/auth/login` | 无 |

**账号管理**

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| 当前用户信息 | GET | `/api/accounts/me` | Bearer |
| 账号列表 | GET | `/api/accounts` | Bearer (admin) |
| 创建账号 | POST | `/api/accounts` | Bearer (admin) |
| 更新账号 | PUT | `/api/accounts/{id}` | Bearer (admin) |
| 冻结账号 | PATCH | `/api/accounts/{id}/freeze` | Bearer (admin) |
| 解冻账号 | PATCH | `/api/accounts/{id}/unfreeze` | Bearer (admin) |
| 重置密码 | PATCH | `/api/accounts/{id}/reset-password` | Bearer (admin) |

**工单系统**

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| 自动创建工单（RAG 降级） | POST | `/api/tickets/auto` | 无 |
| 手动创建工单 | POST | `/api/tickets/manual` | Bearer |
| 工单列表 | GET | `/api/tickets` | Bearer |
| 工单详情 | GET | `/api/tickets/{id}` | Bearer |
| 工单日志 | GET | `/api/tickets/{id}/logs` | Bearer |
| 更新工单 | PUT | `/api/tickets/{id}` | Bearer (operator+) |
| 解决工单 | POST | `/api/tickets/{id}/resolve` | Bearer (operator+) |
| 关闭工单 | POST | `/api/tickets/{id}/close` | Bearer (operator+) |

**知识库**

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| 知识库统计 | GET | `/api/knowledge/stats` | Bearer |
| 知识库列表 | GET | `/api/knowledge` | Bearer |
| 新增条目 | POST | `/api/knowledge` | Bearer |
| 更新条目 | PUT | `/api/knowledge/{id}` | Bearer |
| 删除条目 | DELETE | `/api/knowledge/{id}` | Bearer |

**AI 问答 & 统计**

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| AI 问答（RAG）| POST | `/api/chat` | 无 |
| 仪表盘统计 | GET | `/api/analytics/summary` | Bearer |

完整接口文档：[http://localhost:8000/docs](http://localhost:8000/docs)（Swagger UI）

---

## 环境变量说明

完整模板见 `.env.example`，以下为关键变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://root:342802@localhost:3306/opswarden` | 数据库连接串，**按实际修改** |
| `SECRET_KEY` | `ops-warden-secret-key` | JWT 签名密钥，生产环境必须修改 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token 有效期（分钟） |
| `DEEPSEEK_API_KEY` | _(空)_ | DeepSeek API 密钥，**AI 回答必填** |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 使用的模型 |
| `CHROMA_PATH` | `./chroma_db` | ChromaDB 本地数据目录 |
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | Embedding 模型名（首次自动下载） |
| `RAG_SCORE_THRESHOLD` | `0.4` | 检索相似度阈值（< 此值则触发工单） |
| `RAG_TOP_K` | `3` | 检索返回最大条数 |

生成强密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 团队分工

| 成员 | 负责模块 | 主要文件 |
|---|---|---|
| **A** | AI 核心 / RAG / DeepSeek | `backend/app/rag/` · `backend/smoke_test_rag.py` |
| **B** | 后端业务 / 账号 / 工单 / 数据库 | `backend/app/api/` · `backend/app/models/` · `init.sql` |
| **C** | 前端全部页面 | `frontend/pages/` |
| **D** | 飞书集成 / Docker / 云服务器 | `docker-compose.yml` · 飞书 Webhook |

---

## FAQ / 已知问题

**Q: 登录报 `ValueError: password cannot be longer than 72 bytes`？**

A: passlib 1.7.4 与 bcrypt >= 4.0 的兼容性问题。已在 `backend/app/main.py` 顶部添加补丁修复，确认文件最顶部有如下代码：
```python
import passlib.handlers.bcrypt as _passlib_bcrypt
_passlib_bcrypt.detect_wrap_bug = lambda ident: False
```

**Q: 后端启动报 `ModuleNotFoundError: No module named 'chromadb'`？**

A: 使用了错误的 Python 环境。改用 `python -m uvicorn app.main:app` 启动，确保使用已安装 chromadb 的 Python 环境（通常是 Anaconda）。

**Q: 后端启动报 `[WinError 10048]` 端口占用？**

A: 上次进程未正常退出。执行 `taskkill /F /IM python.exe /T` 清理后重启。

**Q: AI 回答正常但没有 DeepSeek 的生成内容？**

A: `.env` 中 `DEEPSEEK_API_KEY` 未填写。RAG 检索仍会工作，但 LLM 调用被跳过，返回知识库原始文本。

**Q: 后端启动报 `Access denied for user 'ops'@'localhost'`？**

A: 数据库未初始化或 `ops` 用户缺少 `@localhost` 授权。执行：
```sql
CREATE USER IF NOT EXISTS 'ops'@'localhost' IDENTIFIED BY 'ops123456';
GRANT ALL PRIVILEGES ON opswarden.* TO 'ops'@'localhost';
FLUSH PRIVILEGES;
```

**Q: 前端 `npm run dev` 报 `Cannot find module` 错误？**

A: 先运行 `cd frontend && npm install` 安装依赖，再执行 `npm run dev`。

**Q: 浏览器显示"无法连接到后端服务"？**

A: 确认后端已在 8000 端口运行（`curl http://localhost:8000/health`）。开发环境下 Vite 已自动代理 `/api → :8000`，无需配置 CORS。

**Q: 前端页面跳转到 login 但已登录？**

A: 清除浏览器 localStorage 后重新登录（F12 → Application → Local Storage → 清空）。

**Q: Docker 启动报端口 3306 冲突？**

A: 停止本机 MySQL 服务，或改用[本地部署方式](#快速开始本地无需-docker)直接使用本机 MySQL。

---

*OpsWarden · Ver 1.0 · 课题六：运维数字员工的建设*
