# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于本地部署 DeepSeek + RAG + FastAPI + PostgreSQL

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi\&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql\&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-extension-111111)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs\&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite\&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?logo=tailwindcss\&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-auth-000000?logo=jsonwebtokens\&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

***

### 系统机制图

![系统机制图](docs/canva.png)

***

## 目录

- [项目简介](#项目简介)
- [项目亮点](#项目亮点)
- [演示与交互可视化](#演示与交互可视化)
- [快速开始（本地）](#快速开始本地无需-docker)
- [RAG 模块说明](#rag-模块说明)
- [Docker 部署](#docker-部署)
- [目录结构](#目录结构)
- [API 接口](#api-接口)
- [环境变量说明](#环境变量说明)
- [团队分工](#团队分工)
- [FAQ / 已知问题](#faq--已知问题)

**更多文档**：[后端设计 docs/backend.md](docs/backend.md) · [API 测试 docs/API\_TESTING.md](docs/API_TESTING.md) · 协作者/AI 速览见 [CLAUDE.md](CLAUDE.md)（与 README 有重叠，择一详读即可）

***

## 项目简介

> **一句话**：会回答、会建单、**会自己学习** —— 这才是真正的运维数字员工。

**背景**：随着企业信息化不断深入，IT 运维要承接大量重复、标准化的用户咨询（系统访问异常、权限申请、常见故障排查等）。传统人工运维**响应慢、成本高、知识分散难复用**。OpsWarden 以大语言模型（LLM）+ 检索增强生成（RAG）为核心，构建一套面向企业内部运维场景、能**自动解答用户问题、管理工单全生命周期、并持续自我学习**的 AI 智能系统，用 AI 替代重复性运维咨询，从根本上提升运维服务效率与质量。

OpsWarden 的核心功能三条线：

- **AI 问答（RAG）**：用户提问 → **双层检索**（量化锚点 Top-K → 页级条目精排）→ **本地部署 DeepSeek 大模型** 生成回答；知识库无答案时自动创建工单
- **工单系统**：工单全生命周期管理（待处理 → 处理中 → 已解决 → 已关闭），支持解决方案写回知识库
- **账号管理**：运维账号增删改查、冻结/解冻、重置密码，后台可视化管理

**自学习闭环**——这是 OpsWarden 区别于普通问答机器人的关键：

```
用户提问 → RAG 未命中 → （确认后）自动建工单 → 运维解决并勾选「写入知识库」
        ↑                                                    │
        └──────────────  下次同类问题直接命中  ←── 向量化 + 建锚点 ┘
```

> "Ops" stands for Operations — the domain this system serves.
> "Warden" means a guardian or keeper — someone who watches over,
> manages, and protects. Together, OpsWarden means a guardian of
> operations: an AI agent that stands watch over IT workflows,
> handles repetitive tasks, and escalates when human judgment is
> needed.

> **技术栈**

| 层次           | 技术                                  | 版本/说明                                                                 |
| ------------ | ----------------------------------- | --------------------------------------------------------------------- |
| 后端框架         | FastAPI + Uvicorn                   | 0.115 / 0.30                                                          |
| ORM          | SQLAlchemy + psycopg3               | 2.0 / 3.1+                                                            |
| 认证           | JWT (python-jose + passlib)         | HS256                                                                 |
| AI 大模型       | DeepSeek（**本地部署**）                  | OpenAI 兼容接口（vLLM / Ollama / LM Studio 等），不依赖外部 API                     |
| 向量存储         | PostgreSQL pgvector                 | **L1** `kb_anchors` 建 IVFFlat；**L2** `kb_entries.embedding` 仅精排、无向量索引 |
| Embedding 模型 | BAAI/bge-small-zh-v1.5              | sentence-transformers, 512 维                                          |
| 对话编排         | LangGraph + Postgres checkpoint     | 多轮对话状态与 checkpoint 持久化                                                |
| 前端           | Vue 3 + Vite + Pinia + Vue Router 4 | Tailwind CSS 3                                                        |
| 数据库          | PostgreSQL                          | 16（含 pgvector 扩展）                                                     |
| 运行时          | Python                              | 3.11 (Anaconda)                                                       |

***

## 项目亮点

| 亮点               | 说明                                                                       |
| ---------------- | ------------------------------------------------------------------------ |
| **两阶段检索**        | L1 量化锚点粗筛（IVFFlat 路由）+ L2 全精度余弦精排，避免在大表上维护动态索引，**又快又准**                  |
| **自学习闭环**        | 工单解决后一键回写知识库，自动向量化建锚点，**越用越聪明**                                          |
| **精确反学习**        | 每条知识带 `doc_id` / `page_index`，可按文档/页**精准删除**，无需重建整个向量索引                  |
| **优雅降级**         | LLM、LangGraph Agent 任意环节失效都有兜底（回退经典 RAG 管线 / 返回知识库原文），**绝不崩**          |
| **安全工单策略**       | 未命中不静默建单，**需用户确认**后才创建，避免噪声工单                                            |
| **三级角色权限**       | `user`（仅 AI 问答）< `operator`（+工单/知识库/统计）< `admin`（+账号管理），路由守卫 + 接口双重校验 |

***

## 演示与交互可视化

`presentation/` 目录提供一套用于答辩与快速理解本项目的演示材料，**直接用浏览器打开 HTML 即可**（纯前端、零依赖、可离线；`rag-math.html` 的公式渲染需联网加载 MathJax CDN）：

| 文件                                  | 用途                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| [`presentation/rag-interactive.html`](presentation/rag-interactive.html) | **RAG 底层原理交互演示** —— 输入运维问题，实时演示「向量化 → 量化锚点粗筛 → 全精度精排 → 阈值判定 → 命中生成 / 未命中建单」全流程；相似度由浏览器实时计算，支持单步讲解与「回写知识库后重试」的自学习闭环 |
| [`presentation/rag-math.html`](presentation/rag-math.html) | **RAG 数学求解原理解读** —— 用 MathJax 渲染公式，分 6 步讲清 embedding（L2 归一化 / 非对称编码）、联合向量、余弦=点积、两阶段检索（量化 + 锚点路由 + 精排）、阈值判定、条件生成（温度 softmax）的数学本质，并给出端到端求解链与自学习闭环 |

> 想最快建立直觉？先打开 **`presentation/rag-interactive.html`** 跑几条示例问题（绿点=知识库已有 / 红点=未覆盖），再看 **`presentation/rag-math.html`** 对照公式理解每一步背后的数学。

***

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
- 创建所有 ENUM 类型和表（`accounts`、`tickets`、`ticket_logs`、**`kb_anchors`**、**`kb_entries`**）
- **知识库双层存储**：`kb_anchors` 存量化锚点向量（**仅此表**对 `anchor_vec` 建 IVFFlat）；`kb_entries` 存切片正文、`doc_id` / `page_index`、`anchor_id` 外键及 **精排用** `embedding`（**不在此列建 ANN 索引**）
- 插入默认管理员账号：用户名 `admin`，密码 `admin123`

> **从旧版单表结构升级**：若数据库已存在仅含 `kb_entries` + `idx_kb_embedding` 的旧库，请在维护窗口执行 [`scripts/migrate_kb_anchors.sql`](scripts/migrate_kb_anchors.sql)，并通过界面重新保存条目或离线脚本为存量数据回填锚点与向量。

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少填写以下字段：
```

| 变量                  | 默认值                                                          | 是否必填             |
| ------------------- | ------------------------------------------------------------ | ---------------- |
| `DATABASE_URL`      | `postgresql+psycopg://postgres:...@localhost:5432/opswarden` | 是（按实际修改）         |
| `JWT_SECRET_KEY`    | `CHANGE_ME_USE_RANDOM_STRING`                                | 建议修改             |
| `DEEPSEEK_BASE_URL` | `http://localhost:11434/v1`                                  | 是（本地模型服务地址）      |
| `DEEPSEEK_MODEL`    | `deepseek-r1`                                                | 是（与本地部署的模型名一致）   |
| `DEEPSEEK_API_KEY`  | *(空)*                                                        | 否（本地部署可留空或填占位符） |

> **本地大模型说明**：本项目通过 **OpenAI 兼容接口**调用本地部署的 DeepSeek 模型（后端实际请求 `{DEEPSEEK_BASE_URL}/chat/completions`）。用 Ollama 时地址形如 `http://localhost:11434/v1`、模型名形如 `deepseek-r1`；用 vLLM / LM Studio 时按各自暴露的端口与模型名填写即可，无需外网 API Key。

### 5. 启动后端

```bash
cd backend
# 必须使用 python -m uvicorn（确保使用正确的 Python 环境）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：访问 <http://localhost:8000/health>，应返回：

```json
{"status": "healthy", "database": "connected", "vector_store": "ok", "vector_docs": 100}
```

API 文档：<http://localhost:8000/docs>

### 6. 启动前端

新开一个终端，在 `frontend/` 目录执行：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 <http://localhost:5173>，使用 `admin` / `admin123` 登录。

> **注意**：Vite 开发服务器已配置 `/api` 代理到 `http://localhost:8000`，无需手动处理 CORS。

**生产构建：**

```bash
cd frontend
npm run build
# 输出到项目根目录的 dist/ 文件夹
```

***

## RAG 模块说明

- **ICML 2025论文灵感**：[Fast Exact Unlearning for In-Context Learning Data for LLMs](https://arxiv.org/abs/2402.00751)
- **Github开源仓库灵感**：https://github.com/VectifyAI/PageIndex

### 架构概览（量化锚点 + 页级索引）

检索分为两阶段，避免在条目表上维护大型动态聚类索引，便于按 `doc_id` / `page_index` **精确遗忘**切片：

```
用户提问
  │
  ▼
POST /api/chat
  │
  ├─► embed_query()           # BGE 将问题编码为 512 维向量
  │       ↓
  ├─► L1 锚点路由             # 在 kb_anchors.anchor_vec 上做 Top-K（IVFFlat + cosine）
  │       ↓
  ├─► L2 候选精排             # anchor_id ∈ Top-K 的 kb_entries，用条目 embedding 与 query 算相似度
  │       ↓                   # score ≥ RAG_SCORE_THRESHOLD（默认 0.65）即命中
  ├─► [命中] → 本地 DeepSeek 大模型 → 返回 source="kb"
  │
  └─► [未命中] → 工单降级逻辑   → 返回 source="fallback"
```

### 向量存储与写入

- **`kb_anchors`**：条目向量经网格量化 ( \mathrm{round}(v/\epsilon)\cdot\epsilon ) 后 **upsert**，`quant_key` 去重；**ANN 索引只建在锚点表**。
- **`kb_entries`**：`doc_id`、`page_index` 标识文档与页码；`embedding` 保存原始向量供 **L2 精排**，**不在该列创建 IVFFlat/HNSW**。
- **写入**：`retriever.ingest_kb_entry()` 在完成锚点归属后更新条目的 `anchor_id` 与 `embedding`。
- **删除**：删除条目行后，若无其它条目引用同一锚点，则删除孤立 `kb_anchors` 行；支持 `DELETE /api/knowledge/by-doc` 按文档或页批量删除。
- **FAQ**：首次启动从 `knowledge_base/OpsWarden_FAQ.md` 导入，`doc_id=OpsWarden_FAQ`，`page_index` 为条目序号。

### 依赖项检查

```bash
python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
python -c "from pgvector.sqlalchemy import Vector; print('pgvector OK')"
python -c "import httpx; print('httpx OK')"
```

***

## Docker 部署

本项目采用 **一键部署** 方案，使用 Docker Compose 管理所有服务（PostgreSQL + 后端 + 前端），只需维护 Docker 容器即可满足生产部署需求。

### 首次启动

```bash
# 一键启动所有服务（PostgreSQL + 后端 + 前端）
docker compose up -d

# 查看运行状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 代码更新后重启

当你修改了代码（后端 Python 或前端 Vue）后，需要重新构建镜像并重启容器：

```bash
# 停止容器（保留数据）
docker compose down

# 重新构建镜像（检测 Dockerfile 和源码变化）
docker compose build

# 重新启动容器
docker compose up -d

# 查看启动日志，确认服务正常
docker compose logs -f backend
```

### 常用命令

```bash
# 停止服务（保留数据）
docker compose down

# 停止并清除所有数据（慎用！会删除数据库）
docker compose down -v

# 查看容器日志
docker compose logs -f          # 所有服务
docker compose logs -f backend  # 仅后端
docker compose logs -f frontend # 仅前端

# 重启单个服务（如仅后端代码更新）
docker compose up -d --no-deps backend

# 进入数据库容器（调试用）
docker exec -it opswarden-postgres psql -U postgres -d opswarden
```

> **说明**：
>
> - `pgvector/pgvector:pg16` 镜像已预装 pgvector 扩展，`init.sql` 会在容器首次启动时自动执行。
> - 数据库数据持久化存储在 `postgres_data` volume 中，重启容器不会丢失数据。
> - HuggingFace 模型缓存存储在 `hf_cache` volume 中，避免每次构建重复下载。

### 访问地址

| 服务     | 地址                             |
| ------ | ------------------------------ |
| 前端应用   | <http://localhost:8080>        |
| 后端 API | <http://localhost:8000>        |
| API 文档 | <http://localhost:8000/docs>   |
| 健康检查   | <http://localhost:8000/health> |

***

## 目录结构

```
OpsWarden/
├── backend/
│   ├── Dockerfile               # 后端容器构建
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
│       │   └── chat.py          # AI 问答入口（LangGraph + RAG + 工单降级）
│       ├── middleware/
│       │   ├── auth.py          # JWT 鉴权
│       │   ├── exception.py     # 统一异常处理
│       │   └── logging.py       # 请求日志
│       ├── models/
│       │   ├── account.py       # Account ORM 模型
│       │   ├── ticket.py        # Ticket / TicketLog ORM 模型
│       │   └── knowledge.py     # KBAnchor / KBEntry（锚点与页级条目）
│       ├── schemas/
│       │   ├── account.py
│       │   ├── ticket.py
│       │   └── knowledge.py
│       ├── utils/
│       │   ├── response.py      # 统一响应格式
│       │   ├── security.py      # 密码哈希 / JWT 工具
│       │   └── employee_id.py   # 按角色生成工号（ADM/OPS/USR + 序号）
│       ├── graphs/
│       │   └── chat_workflow.py # LangGraph 对话编排（Postgres checkpoint）
│       ├── checkpointer/        # LangGraph Postgres checkpoint 连接与工具
│       └── rag/
│           ├── embedder.py      # Sentence-Transformers 封装
│           ├── quantizer.py     # 向量量化（锚点网格 ε）
│           ├── faq_loader.py    # Markdown FAQ 解析 → PostgreSQL
│           ├── llm.py           # 本地 DeepSeek 大模型调用（OpenAI 兼容接口）
│           ├── retriever.py     # 双阶段检索 + ingest_kb_entry / prune_anchor
│           └── chat_pipeline.py # RAG 管道（供工作流节点调用）
├── frontend/                    # Vue 3 + Vite SPA
│   ├── Dockerfile               # 前端静态资源 + nginx 容器
│   ├── nginx.conf
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
├── docker/
│   └── engine-ipv4-snippet.json # Docker Engine IPv4 优先片段（排障见 scripts）
├── scripts/
│   ├── docker_verify_log.py     # compose 校验与日志采集
│   └── migrate_kb_anchors.sql   # 旧库升级到锚点架构（可选）
├── docs/
│   ├── canva.png                # 系统流程图（可替换为高分辨率版本）
│   ├── API_TESTING.md           # API 测试文档
│   └── backend.md               # 后端设计文档
├── presentation/                # 答辩演示与可视化（纯前端、可离线）
│   ├── index.html               # 答辩主稿 slides（reveal.js）
│   ├── rag-interactive.html     # RAG 底层原理交互演示（实时算相似度）
│   └── rag-math.html            # RAG 数学求解原理解读（MathJax 公式）
├── init.sql                     # 数据库初始化脚本（PostgreSQL + pgvector）
├── requirements.txt             # Python 依赖
├── docker-compose.yml           # Docker 编排（PostgreSQL + pgvector）
├── .env.example                 # 环境变量模板（运行时复制为 .env）
└── README.md
```

***

## API 接口

所有接口基础路径：`http://localhost:8000`

**认证**

| 接口 | 方法   | 路径                | 认证 |
| -- | ---- | ----------------- | -- |
| 登录 | POST | `/api/auth/login` | 无  |

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

创建账号时 **`employee_id`** **可省略**：服务端按所选角色自动生成工号（`ADM#####` / `OPS#####` / `USR#####`）；也可显式传入自定义工号（须全局唯一）。

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

创建/更新条目时可传 **`doc_id`、`page_index`**（页级索引）；列表支持 **`doc_id`** 筛选查询参数。

| 接口      | 方法     | 路径                                                   | 认证     |
| ------- | ------ | ---------------------------------------------------- | ------ |
| 知识库统计   | GET    | `/api/knowledge/stats`                               | Bearer |
| 快捷题目列表  | GET    | `/api/knowledge/quick-prompts`                       | Bearer |
| 知识库列表   | GET    | `/api/knowledge`                                     | Bearer |
| 新增条目    | POST   | `/api/knowledge`                                     | Bearer |
| 更新条目    | PUT    | `/api/knowledge/{id}`                                | Bearer |
| 按 id 删除 | DELETE | `/api/knowledge/{id}`                                | Bearer |
| 按文档删除   | DELETE | `/api/knowledge/by-doc`（`doc_id` 必填，`page_index` 可选） | Bearer |

**AI 问答 & 统计**

| 接口         | 方法   | 路径                       | 认证     |
| ---------- | ---- | ------------------------ | ------ |
| AI 问答（RAG） | POST | `/api/chat`              | Bearer |
| 仪表盘统计      | GET  | `/api/analytics/summary` | Bearer |

完整接口文档：<http://localhost:8000/docs>（Swagger UI）

***

## 环境变量说明

完整模板见 `.env`，以下为关键变量：

| 变量                                | 默认值                                                          | 说明                             |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------ |
| `DATABASE_URL`                    | `postgresql+psycopg://postgres:...@localhost:5432/opswarden` | 数据库连接串，**按实际修改**               |
| `JWT_SECRET_KEY`                  | `CHANGE_ME_USE_RANDOM_STRING`                                | JWT 签名密钥，生产环境必须修改              |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `480`                                                        | Token 有效期（分钟）                  |
| `DEEPSEEK_BASE_URL`               | `http://localhost:11434/v1`                                  | **本地模型服务地址**（OpenAI 兼容），如 Ollama / vLLM / LM Studio |
| `DEEPSEEK_MODEL`                  | `deepseek-r1`                                                | 本地部署的模型名（与服务端一致）               |
| `DEEPSEEK_API_KEY`                | _(空)_                                                        | 本地部署通常无需，可留空或填占位符            |
| `EMBEDDING_MODEL`                 | `BAAI/bge-small-zh-v1.5`                                     | Embedding 模型名（首次自动下载）          |
| `RAG_SCORE_THRESHOLD`             | `0.65`                                                       | L2 精排相似度阈值（≥ 命中，否则走工单降级）；经调优由 0.4 上调至 **0.65**，FPR 大幅下降，详见 [调优报告](docs/rag_hyperparam_report_v3_joint.md) |
| `RAG_TOP_K`                       | `3`                                                          | 最终返回知识切片条数上限                   |
| `RAG_ANCHOR_TOP_K`                | `8`                                                          | L1 锚点路由 Top-K                  |
| `ANCHOR_QUANT_EPSILON`            | `0.02`                                                       | 锚点网格量化步长 (\epsilon)（`.env` 可调） |

生成强密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

***

## 团队分工

| 成员             | 负责模块                   | 主要文件                                                    |
| -------------- | ---------------------- | ------------------------------------------------------- |
| **廖晨扬**        | AI 核心 / RAG / DeepSeek | `backend/app/rag/`                                      |
| **吴雨彤**        | 后端业务 / 账号 / 工单 / 数据库   | `backend/app/api/` · `backend/app/models/` · `init.sql` |
| **廖晨扬+Stitch** | 前端全部页面                 | `frontend/`                                             |
| **丁其彬**        | Docker / 云服务器 / 申请域名   | `docker-compose.yml`                                    |

***

## FAQ / 已知问题

**Q: 后端启动报** **`ModuleNotFoundError: No module named 'psycopg'`？**

A: 使用了错误的 Python 环境。改用 `python -m uvicorn app.main:app` 启动，确保使用已安装依赖的 Python 环境（通常是 Anaconda）。

**Q: 后端启动报** **`[WinError 10048]`** **端口占用？**

A: 上次进程未正常退出。执行 `taskkill /F /IM python.exe /T` 清理后重启。

**Q: AI 回答正常但没有 DeepSeek 的生成内容？**

A: 本地 DeepSeek 模型服务未启动，或 `.env` 中 `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` 配置与本地服务不一致。RAG 检索仍会工作（优雅降级），但 LLM 生成被跳过，直接返回知识库原始文本。排查：确认本地模型服务已运行（如 `curl http://localhost:11434/v1/models`），且模型名与 `DEEPSEEK_MODEL` 一致。

**Q: pgvector 扩展安装失败？**

A: 需要 Visual Studio Build Tools（含 C++ 工具集）。以管理员身份打开"x64 Native Tools Command Prompt for VS 2022"，并确保 `PGROOT` 指向正确的 PostgreSQL 安装目录。

**Q:** **`psql`** **执行 init.sql 报编码错误（GBK/UTF8）？**

A: Windows 终端默认 GBK 编码与 PostgreSQL UTF8 不兼容。执行前运行：

```cmd
set PGCLIENTENCODING=UTF8
psql -U postgres -d opswarden -f init.sql
```

**Q: 健康检查返回** **`vector_store: error`？**

A: pgvector 扩展未正确安装或未在数据库中启用。确认执行过 `CREATE EXTENSION IF NOT EXISTS vector;`，可在 psql 中运行 `\dx` 查看已安装扩展。

**Q: 升级数据库后 AI 检索不到知识库条目？**

A: 若为从旧版「单表 IVFFlat」迁移而来，请确认已执行 `scripts/migrate_kb_anchors.sql`，并在后台 **重新编辑保存** 各条目（或运行回填脚本），使 `kb_anchors` 与条目的 `embedding`/`anchor_id` 完整写入。

**Q: 前端** **`npm run dev`** **报** **`Cannot find module`** **错误？**

A: 先运行 `cd frontend && npm install` 安装依赖，再执行 `npm run dev`。

**Q: 浏览器显示"无法连接到后端服务"？**

A: 确认后端已在 8000 端口运行（`curl http://localhost:8000/health`）。开发环境下 Vite 已自动代理 `/api → :8000`，无需配置 CORS。

**Q: 前端页面跳转到 login 但已登录？**

A: 清除浏览器 localStorage 后重新登录（F12 → Application → Local Storage → 清空）。

***

*OpsWarden · Ver 1.0 · 课题六：运维数字员工的建设*
