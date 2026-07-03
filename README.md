# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于本地部署 Qwen2.5:1.5b + RAG + FastAPI + PostgreSQL

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

## 项目简介

> **一句话**：会回答、会建单、**会自己学习** —— 这才是真正的运维数字员工。

**背景**：随着企业信息化不断深入，IT 运维要承接大量重复、标准化的用户咨询（系统访问异常、权限申请、常见故障排查等）。传统人工运维**响应慢、成本高、知识分散难复用**。OpsWarden 以大语言模型（LLM）+ 检索增强生成（RAG）为核心，构建一套面向企业内部运维场景、能**自动解答用户问题、管理工单全生命周期、并持续自我学习**的 AI 智能系统，用 AI 替代重复性运维咨询，从根本上提升运维服务效率与质量。

OpsWarden 的核心功能三条线：

- **AI 问答（RAG）**：用户提问 → **双层检索**（量化锚点 Top-K → 页级条目精排）→ **本地部署 Qwen2.5:1.5b 大模型** 生成回答；知识库无答案时自动创建工单
- **工单系统**：工单全生命周期管理（待处理 → 处理中 → 已解决 → 已关闭），支持解决方案写回知识库
- **账号管理**：运维账号增删改查、冻结/解冻、重置密码，后台可视化管理

**自学习闭环**——这是 OpsWarden 区别于普通问答机器人的关键：

```
用户提问 → RAG 未命中 → （确认后）自动建工单 → 运维解决并勾选「写入知识库」
        ↑                                                    │
        └──────────────  下次同类问题直接命中  ←── 向量化 + 建锚点 ┘
```

## 技术栈

| 层次           | 技术                                  | 版本/说明                                                                 |
| ------------ | ----------------------------------- | --------------------------------------------------------------------- |
| 后端框架         | FastAPI + Uvicorn                   | 0.115 / 0.30                                                          |
| ORM          | SQLAlchemy + psycopg3               | 2.0 / 3.1+                                                            |
| 认证           | JWT (python-jose + passlib)         | HS256                                                                 |
| AI 大模型       | Qwen2.5:1.5b（**本地部署**）               | OpenAI 兼容接口（vLLM / Ollama / LM Studio 等），不依赖外部 API                     |
| 向量存储         | PostgreSQL pgvector                 | **L1** `kb_anchors` 建 IVFFlat；**L2** `kb_entries.embedding` 仅精排、无向量索引 |
| Embedding 模型 | BAAI/bge-small-zh-v1.5              | sentence-transformers, 512 维                                          |
| 对话编排         | LangGraph + Postgres checkpoint     | 多轮对话状态与 checkpoint 持久化                                                |
| 前端           | Vue 3 + Vite + Pinia + Vue Router 4 | Tailwind CSS 3                                                        |
| 数据库          | PostgreSQL                          | 16（含 pgvector 扩展）                                                     |
| 运行时          | Python                              | 3.11 (Anaconda)                                                       |

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

## 项目启动准备

### 前置要求

- Python 3.11+（**推荐 Anaconda**，因 sentence-transformers 需要完整环境）
- PostgreSQL 16（本地已运行，**含 pgvector 扩展**）
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

> sentence-transformers 较大，首次安装需要几分钟。首次启动时还会自动下载 `BAAI/bge-small-zh-v1.5` 模型（约 100 MB）。

### 3. 安装 PostgreSQL 16 + pgvector（Windows）

> 已安装并启用 pgvector 的可跳过此节。

前往 [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) 下载 PostgreSQL 16 并安装。pgvector 需从源码编译：

```cmd
::: 1. 下载源码：https://github.com/pgvector/pgvector/archive/refs/tags/v0.8.2.zip
::: 2. 用管理员身份打开 "x64 Native Tools Command Prompt for VS 2022"
::: 3. 设置 PostgreSQL 安装路径并编译
set "PGROOT=D:\PostgreSQL\16"
nmake /f Makefile.win
nmake /f Makefile.win install
```

### 4. 初始化数据库

```bash
createdb -U postgres opswarden
set PGCLIENTENCODING=UTF8
psql -U postgres -d opswarden -f init.sql
```

`init.sql` 会自动完成：启用 `vector` 扩展、创建所有表（含 `kb_anchors` / `kb_entries` 双层存储）、插入默认管理员 `admin` / `admin123`。

### 5. 配置环境变量

```bash
cp .env.example .env
```

关键变量：

| 变量                  | 默认值                                                          | 是否必填             |
| ------------------- | ------------------------------------------------------------ | ---------------- |
| `DATABASE_URL`      | `postgresql+psycopg://postgres:...@localhost:5432/opswarden` | 是（按实际修改）         |
| `JWT_SECRET_KEY`    | `CHANGE_ME_USE_RANDOM_STRING`                                | 建议修改             |
| `DEEPSEEK_BASE_URL` | `http://localhost:11434/v1`                                  | 是（本地模型服务地址）      |
| `DEEPSEEK_MODEL`    | `qwen2.5:1.5b`                                               | 是（与本地部署的模型名一致）   |
| `DEEPSEEK_API_KEY`  | *(空)*                                                        | 否（本地部署可留空） |

> 通过 **OpenAI 兼容接口**调用本地部署的 Qwen2.5:1.5b 模型。用 Ollama 时地址形如 `http://localhost:11434/v1`；用 vLLM / LM Studio 时按各自端口与模型名填写即可，无需外网 API Key。

***

## 项目前后端启动

### 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

验证：访问 <http://localhost:8000/health>，应返回 `{"status": "healthy", ...}`。API 文档：<http://localhost:8000/docs>

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 <http://localhost:5173>，使用 `admin` / `admin123` 登录。Vite 开发服务器已配置 `/api` 代理到 `http://localhost:8000`，无需手动处理 CORS。

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
  ├─► [命中] → 本地 Qwen2.5:1.5b 大模型 → 返回 source="kb"
  │
  └─► [未命中] → 工单降级逻辑   → 返回 source="fallback"
```

### 向量存储与写入

- **`kb_anchors`**：条目向量经网格量化 \( \mathrm{round}(v/\epsilon)\cdot\epsilon \) 后 **upsert**，`quant_key` 去重；**ANN 索引只建在锚点表**。
- **`kb_entries`**：`doc_id`、`page_index` 标识文档与页码；`embedding` 保存原始向量供 **L2 精排**，**不在该列创建 IVFFlat/HNSW**。
- **写入**：`retriever.ingest_kb_entry()` 在完成锚点归属后更新条目的 `anchor_id` 与 `embedding`。
- **删除**：删除条目行后，若无其它条目引用同一锚点，则删除孤立 `kb_anchors` 行；支持 `DELETE /api/knowledge/by-doc` 按文档或页批量删除。
- **FAQ**：首次启动从 `knowledge_base/OpsWarden_FAQ.md` 导入，`doc_id=OpsWarden_FAQ`，`page_index` 为条目序号。

***

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
│           ├── llm.py           # 本地 Qwen2.5:1.5b 大模型调用（OpenAI 兼容接口）
│           ├── retriever.py     # 双阶段检索 + ingest_kb_entry / prune_anchor
│           └── chat_pipeline.py # RAG 管道（供工作流节点调用）
├── frontend/                    # Vue 3 + Vite SPA
│   ├── index.html               # Vite 入口
│   ├── package.json
│   ├── vite.config.js           # 代理 /api → :8000
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
├── scripts/
│   └── migrate_kb_anchors.sql   # 旧库升级到锚点架构（可选）
├── docs/
│   ├── canva.png                # 系统流程图
│   ├── API_TESTING.md           # API 测试文档
│   └── backend.md               # 后端设计文档
├── presentation/                # 答辩演示与可视化（纯前端、可离线）
│   ├── index.html               # 答辩主稿 slides（reveal.js）
│   ├── rag-interactive.html     # RAG 底层原理交互演示
│   └── rag-math.html            # RAG 数学求解原理解读（MathJax 公式）
├── init.sql                     # 数据库初始化脚本（PostgreSQL + pgvector）
├── requirements.txt             # Python 依赖
├── docker-compose.yml           # Docker 编排
├── .env.example                 # 环境变量模板
└── README.md
```

***

## 团队分工

| 成员             | 负责模块                   | 主要文件                                                    |
| -------------- | ---------------------- | ------------------------------------------------------- |
| **廖晨扬**        | AI 核心 / RAG / 敏捷开发统筹  | `backend/app/rag/`                                      |
| **吴雨彤**        | 后端业务 / 账号 / 工单 / 数据库   | `backend/app/api/` · `backend/app/models/` · `init.sql` |
| **廖晨扬+Stitch** | 前端全部页面                 | `frontend/`                                             |
| **丁其彬**        | Docker / 云服务器 / Qwen2.5:1.5b | `backend/app/rag/` · `backend/app/models/` · `init.sql` | `docker-compose.yml`                                    |

***

*OpsWarden · 课题六：运维数字员工的建设*
