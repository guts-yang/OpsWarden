# OpsWarden — CLAUDE.md

AI 运维数字员工平台。用户通过 AI 问答处理运维问题，命中知识库则 Ollama 生成答案，未命中则需用户确认后创建工单；工单解决可写回知识库形成自学习闭环。

---

## 项目结构

```
OpsWarden/
├── backend/app/
│   ├── main.py           # 入口，注册路由/中间件/启动 FAQ 与 checkpointer
│   ├── config.py         # Settings（pydantic-settings，读取根目录 .env）
│   ├── database.py       # SQLAlchemy engine、SessionLocal、get_db()
│   ├── api/              # auth, account, ticket, analytics, knowledge, chat
│   ├── agent/            # LangGraph Agent（graph, llm, tools, policy, trace）
│   ├── models/           # account, ticket, knowledge（KBAnchor/KBEntry）
│   ├── schemas/          # Pydantic 请求/响应
│   ├── middleware/       # auth（JWT）、exception、logging
│   ├── rag/              # embedder, retriever, llm, faq_loader, chat_pipeline
│   ├── graphs/           # chat_workflow（LangGraph checkpoint 辅助）
│   ├── checkpointer/     # Postgres checkpoint 连接池
│   └── utils/            # security（bcrypt/JWT）、response、employee_id
├── frontend/src/
│   ├── main.js / App.vue
│   ├── router/index.js   # 路由 + 角色守卫
│   ├── stores/auth.js    # Pinia（ow_token, ow_user）
│   ├── api/              # axios client + 各模块
│   ├── views/            # Login, Dashboard, Accounts, Tickets, AiChat, Knowledge
│   ├── layouts/MainLayout.vue
│   ├── components/       # AppSidebar, AppHeader, AppBottomTabBar, Base*
│   └── utils/            # chatSessionStorage, constants
├── init.sql              # PostgreSQL schema + 默认 admin（bcrypt 占位）
├── import_knowledge.py   # 可选：API 批量导入 FAQ
├── requirements.txt
├── .env.example
└── docker-compose.yml    # postgres + backend + frontend
```

---

## 技术栈

| 层    | 技术                                                            |
| ---- | ------------------------------------------------------------- |
| 后端   | Python 3.11 + FastAPI 0.115 + Uvicorn                         |
| ORM  | SQLAlchemy 2.0，驱动 psycopg3                                    |
| 数据库  | PostgreSQL 16 + pgvector（L1 IVFFlat 锚点 + L2 余弦精排）                |
| AI   | Ollama 本地 API（默认 `qwen2.5:1.5b`）+ BAAI/bge-small-zh-v1.5（512 维） |
| 编排   | LangGraph + Postgres checkpoint + Agent 工具调用                    |
| 前端   | Vue 3 + Vite 6 + Pinia + Vue Router 4 + TailwindCSS 3           |
| HTTP | Axios，响应拦截器解包 `{code, message, data}` 信封                      |

---

## 启动方式

```bash
# Ollama（首次）
ollama pull qwen2.5:1.5b

# 数据库（首次）
docker compose up -d postgres   # 或本地 PostgreSQL
psql -U postgres -d opswarden -f init.sql

# 后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev        # http://localhost:5173
npm run build      # → 项目根 dist/
```

Vite 开发代理：`/api` → `http://localhost:8000`（无路径重写）。

---

## 核心流程

### AI 问答（Agent 优先，RAG 兜底）

```
POST /api/chat { query, thread_id?, pending_action? }
  → LangGraph Agent（Ollama 决策 + 工具调用，最多 5 步）
      工具：kb_search / ticket_* / analytics_summary / system_health_check
      ticket_create 需用户 confirm（pending_action 回传）
  → [Agent 失败] run_chat_pipeline() 经典 RAG 单轮兜底
      → embed_query() → L1 锚点 Top-K → L2 精排（threshold ≥ 0.65）
      → [命中] generate_answer(Ollama) 或返回 solution 原文
      → [未命中] 返回 needs_confirmation + pending_action（不静默建单）
```

### 知识库条目创建

```
POST /api/knowledge { question, solution, doc_id?, page_index?, ... }
  → 写入 kb_entries
  → ingest_kb_entry()：联合向量 + 量化锚点 upsert + 更新 embedding/anchor_id
  → embedding 失败时该条目对 RAG 不可见（embedding IS NULL）
```

### 认证与角色

- JWT（HS256），localStorage：`ow_token`, `ow_user`
- 角色：`admin` > `operator` > `user`
- `user` 仅可访问 AI 问答；`operator` + 工单/知识库/统计；`admin` + 账号管理

---

## API 路由概览

| 路由前缀             | 主要端点                                                      |
| ---------------- | --------------------------------------------------------- |
| `/api/auth`      | `POST /login`                                              |
| `/api/accounts`  | CRUD，`/me`，`/freeze`，`/unfreeze`，`/reset-password`（admin） |
| `/api/tickets`   | `POST /auto`，`/manual`，详情/日志/解决/关闭                         |
| `/api/knowledge` | CRUD，`/stats`，`/quick-prompts`，`DELETE /by-doc`            |
| `/api/chat`      | `POST /`（Agent + RAG，支持 thread_id checkpoint）             |
| `/api/analytics` | `GET /summary`                                             |

---

## 数据模型关键字段

**Account**：`employee_id`（UNIQUE，可按角色自动生成 ADM/OPS/USR 前缀）、`role`、`status`（active/frozen）

**Ticket**：`ticket_no`（`T-YYYYMMDD-NNN`）、`source`（ai_auto/manual）、`status`、`is_written_back`

**KBAnchor**：`quant_key`、`anchor_vec`（512 维，IVFFlat 索引）

**KBEntry**：`doc_id`/`page_index`、`anchor_id`、`embedding`（精排用）、`match_score`（Q-S 自检分）、`source`（manual/ticket_writeback）

**agent_runs / agent_tool_calls**：Agent 审计日志

---

## 环境变量（关键项）

| 变量                            | 说明                          |
| ----------------------------- | --------------------------- |
| `DATABASE_URL`                | PostgreSQL 连接串（psycopg3）    |
| `SECRET_KEY`                  | JWT 签名密钥                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 默认 `480`                    |
| `OLLAMA_BASE_URL`             | 默认 `http://localhost:11434`（不含 /v1） |
| `OLLAMA_MODEL`                | 默认 `qwen2.5:1.5b`           |
| `RAG_SCORE_THRESHOLD`         | 默认 `0.65`                   |
| `RAG_TOP_K` / `RAG_ANCHOR_TOP_K` | 默认 `3` / `8`             |
| `ANCHOR_QUANT_EPSILON`        | 默认 `0.02`                   |

完整列表见 `.env.example` 与 [docs/TECHNICAL.md](docs/TECHNICAL.md)。

---

## 常见问题

**知识库检索不到：** 检查 `kb_entries.embedding` 是否为 NULL；`CURL_CA_BUNDLE` 无效会导致 HuggingFace 模型下载失败（`main.py` 启动时已清除）。

**AI 无生成内容：** 确认 Ollama 已启动且 `OLLAMA_MODEL` 与 `ollama list` 一致。

**无法 admin 登录：** `init.sql` 中密码为 bcrypt 占位符，需替换后重新初始化或更新数据库。

**默认管理员：** username `admin`，password 需在 `init.sql` 中自行设置。
