# OpsWarden — CLAUDE.md

AI 运维数字员工平台。用户通过多轮 AI 问答处理运维问题：命中知识库直接作答，未命中则引导用户确认后生成工单；工单解决后可回写知识库，形成自学习闭环。

> 本文档描述 `main` 分支当前代码状态。仓库内 `docs/backend.md` 已严重过时（仍写 MySQL/pymysql），不要以它为依据。

---

## 项目结构

```
OpsWarden/
├── backend/
│   ├── app/
│   │   ├── main.py            # 入口：注册中间件/异常处理/6 个路由，startup/shutdown 初始化
│   │   ├── config.py          # Settings（pydantic-settings，读仓库根 .env）
│   │   ├── database.py        # engine(pool 10/20)、SessionLocal、Base、init_extensions()、get_db()
│   │   ├── agent/             # ★ LangGraph 受控 Agent（state/graph/llm/prompts/policy/tools/trace）
│   │   ├── checkpointer/      # ★ PostgresSaver（runtime/conninfo/config_helpers）
│   │   ├── graphs/            # 早期单节点 chat 图，已无引用（死代码）
│   │   ├── api/               # 路由：auth, account, ticket, analytics, knowledge, chat
│   │   ├── models/            # ORM：Account / Ticket + TicketLog / KBAnchor + KBEntry
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── middleware/        # auth.py(JWT)、exception.py、logging.py
│   │   ├── rag/               # embedder, quantizer, retriever, llm, chat_pipeline, faq_loader, eval_engine
│   │   └── utils/             # security.py(bcrypt/JWT)、response.py、employee_id.py
│   ├── knowledge_base/OpsWarden_FAQ.md   # 启动时空库自动导入的 FAQ 语料
│   └── Dockerfile             # python:3.11-slim，uvicorn :8000
├── frontend/
│   ├── src/
│   │   ├── main.js            # Vue 入口（Pinia + Router）
│   │   ├── App.vue / style.css # 根组件 + Tailwind 全局样式（MD3 色板）
│   │   ├── router/index.js    # 路由表 + beforeEach 鉴权/角色守卫
│   │   ├── stores/auth.js     # 唯一 Pinia store（token/user + 权限 computed）
│   │   ├── api/               # axios client.js + auth/accounts/tickets/knowledge/chat/analytics
│   │   ├── views/             # Login, Dashboard, Tickets, AiChat, KnowledgeBase, Accounts
│   │   ├── layouts/MainLayout.vue  # Sidebar + Header + RouterView + 移动端 BottomTabBar
│   │   ├── components/        # AppSidebar/AppHeader/AppBottomTabBar/BaseModal/BaseSlidePanel/BasePagination
│   │   └── utils/             # constants.js、chatSessionStorage.js
│   ├── public/fonts/          # 自托管 Material Symbols + 中英文字体（离线可用）
│   ├── Dockerfile             # node:20-alpine 构建 → nginx:alpine 运行
│   ├── nginx.conf             # /api 反代 backend:8000，SPA history fallback
│   ├── vite.config.js         # dev :5173，/api 代理 :8000（无 rewrite），build.outDir = ../dist
│   └── tailwind.config.js / postcss.config.js
├── docs/                      # API_TESTING.md（接口测试手册）、backend.md（过时）、canva.png（机制图）
├── docker/                    # engine-ipv4-snippet.json（Docker 引擎配置片段）
├── init.sql                   # 建表 + ENUM + pgvector + ivfflat 索引 + 默认管理员占位
├── requirements.txt           # 后端依赖（含 RAG 对比实验用的 numpy/rank-bm25/hnswlib 等）
├── docker-compose.yml         # postgres + backend + frontend 三服务
└── README.md                  # 课程设计主文档（含机制图、分工、启动步骤）
```

---

## 技术栈

| 层      | 技术                                                                     |
| ------ | ---------------------------------------------------------------------- |
| 后端     | Python 3.11 + FastAPI 0.115 + Uvicorn                                   |
| ORM    | SQLAlchemy 2.0，驱动 psycopg3                                             |
| 数据库    | PostgreSQL 16 + pgvector（`kb_anchors` 上 ivfflat cosine 索引）                |
| Agent  | LangGraph + `langgraph-checkpoint-postgres`（自建 psycopg 连接池 + PostgresSaver）  |
| LLM    | DeepSeek 兼容 OpenAI 接口（默认本地 `http://localhost:11434/v1`，模型 `deepseek-r1`） |
| 向量     | BAAI/bge-small-zh-v1.5（512 维，本地离线加载 `HF_HUB_OFFLINE=1`）                  |
| 前端     | Vue 3.5 + Vite 6 + Pinia 2.2 + Vue Router 4.5 + TailwindCSS 3（MD3 色板）    |
| 图标/UI  | 自托管 Material Symbols 字体，**无 Element Plus 等组件库**，Base* 组件自研            |
| HTTP   | Axios，响应拦截器解包 `{code, message, data}` 信封                               |

---

## 启动方式

```bash
# 方式一：全容器（推荐演示）
docker compose up -d          # postgres:5432 / backend:8000 / frontend:8080

# 方式二：本地开发
docker compose up -d postgres # 首次启动会自动执行 init.sql
psql -U postgres -d opswarden -f init.sql   # 非容器部署时手动执行

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd frontend
npm run dev        # http://localhost:5173
npm run build      # 产物输出到仓库根 dist/
```

- Vite 开发代理：`/api` → `http://localhost:8000`（无路径重写）。
- 容器访问入口是 `http://localhost:8080`（nginx 反代 `/api` 到 backend）。

---

## 核心流程

### AI 问答（LangGraph Agent，主路径）

```
POST /api/chat {query, thread_id?, pending_action?}
  → thread_id 解析为 "user-{id}-{client_id|default}"
  → 若带 pending_action 且用户回复确认/取消 → 直接执行或放弃（不进图）
  → create_run() 写 agent_runs 审计
  → invoke_agent_with_checkpoint()
      graph: load_context → decide ⇄ tool（最多 5 步）→ final
      decide: DeepSeek JSON 决策（失败则 heuristic 规则兜底）
      tools: kb_search / ticket_search / ticket_get / ticket_create
             / analytics_summary / system_health_check
  → 异常或 saver 不可用 → 回退 run_chat_pipeline（checkpointed=false, agent_enabled=false）
```

- **会话记忆**：由 PostgresSaver 按 `thread_id` 做 checkpoint 持久化（表 `checkpoints*` 运行时由 `saver.setup()` 自动创建，`init.sql` 不含）。
- **安全策略**（`agent/policy.py`）：`ticket_search` / `analytics_summary` 仅 operator/admin；`ticket_create` 必须先经用户二次确认（`needs_confirmation` + `pending_action`）。
- **审计**：每次运行写入 `agent_runs`，每次工具调用写入 `agent_tool_calls`（含 `args_json`/`result_json`/`latency_ms`）。

### 知识库检索（两段式）

```
写入 ingest_kb_entry()
  → 用 (question_vec + solution_vec)/2 归一化作为条目 embedding
  → 量化（eps=0.02）后 SHA256 去重 upsert 到 kb_anchors，写 match_score 自检质量分

检索 search()
  → L1：kb_anchors 上 cosine 近邻（anchor_k=8，ivfflat）
  → L2：锚点关联条目精排，score ≥ RAG_SCORE_THRESHOLD(0.65) 视为命中，取 top_k=3
```

**注意**：`rag/chat_pipeline.py` 是**单轮兜底路径**，明确不会自动建单，只返回 `needs_confirmation`；自动建单能力只在 Agent 图里且需确认。

### 知识库回写

工单 `POST /api/tickets/{id}/resolve?write_back=true` 会以 `source=ticket_writeback` 新建 `KBEntry` 并同步向量/锚点，构成自学习闭环。

### 认证

- JWT（HS256），存于 localStorage（键：`ow_token`, `ow_user`）
- Axios 请求拦截器自动注入 `Authorization: Bearer {token}`
- 401 响应触发自动登出并跳转 `/login`
- 三级角色：`admin` > `operator` > `user`（`user` 角色仅可访问 `/chat`）
- 注册端点已移除，账号由 admin 创建，工号由 `utils/employee_id.py` 按 `ADM/OPS/USR + 5 位序号` 分配
- 首次启动 FAQ 自动导入：`backend/knowledge_base/OpsWarden_FAQ.md`（库非空则跳过）

---

## API 路由概览

| 路由前缀             | 主要端点                                                                                              | 权限       |
| ---------------- | ------------------------------------------------------------------------------------------------- | -------- |
| `/api/auth`      | `POST /login`                                                                                     | 公开       |
| `/api/accounts`  | `GET/PUT /me`、`PATCH /me/password`、CRUD、`/freeze`、`/unfreeze`、`/reset-password`                     | admin（/me 除外） |
| `/api/tickets`   | `POST /auto`（内部调用，无鉴权）、`POST /manual`、列表/详情/日志、`PUT` 更新、`/resolve`、`/callback`、`/close` | operator  |
| `/api/knowledge` | CRUD、`GET /stats`、`GET /quick-prompts`、`DELETE /by-doc`                                           | operator  |
| `/api/chat`      | `POST /`（Agent 问答 + checkpoint）                                                                     | 登录用户     |
| `/api/analytics` | `GET /summary`（仪表盘 7 项指标）                                                                           | operator  |
| `/`、`/health`    | 系统信息、健康检查（DB + 向量库 + vector_docs）                                                                   | 公开       |

Swagger：`http://localhost:8000/docs`（手工测试步骤见 `docs/API_TESTING.md`）。

---

## 数据模型关键字段

**Account**（`accounts`）：`employee_id`（UNIQUE）、`username`（UNIQUE）、`role`（admin/operator/user）、`status`（active/frozen）、`department`（infra/network_security/database_middleware/app_ops/helpdesk/rnd/general）

**Ticket**（`tickets`）：`ticket_no`（`T-YYYYMMDD-NNN`）、`source`（ai_auto/manual/feishu）、`status`（pending/processing/resolved/closed）、`priority`（low/medium/high/urgent）、`is_written_back`
**TicketLog**（`ticket_logs`）：`ticket_id` FK CASCADE、`action`、`operator_id/name`、`content`

**KBAnchor**（`kb_anchors`）：`quant_key`（UNIQUE，量化向量 SHA256）、`anchor_vec` vector(512)，L1 检索层
**KBEntry**（`kb_entries`）：`question`、`solution`、`category`、`tags`、`source`（manual/ticket_writeback/document）、`match_score`（自检质量分）、`anchor_id` FK、`doc_id`/`page_index`（精确反学习）、`embedding` vector(512，NULL 则 RAG 不可见）

**Agent 审计表**（非 ORM，DDL 见 `app/agent/trace.py` 与 `init.sql`）：
- `agent_runs`：`thread_id`、`user_id`、`query`、`final_answer`、`stop_reason`
- `agent_tool_calls`：`run_id` FK CASCADE、`tool_name`、`args_json`、`result_json`、`latency_ms`、`success`

业务表全部由 `init.sql` 建立（代码内**无** `create_all`）；LangGraph `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` 由 `PostgresSaver.setup()` 运行时创建。

---

## 统一响应格式

所有接口统一返回：

```json
{ "code": 200, "message": "...", "data": {...} }
```

错误码：400 参数错误、401 未认证、403 权限不足、404 资源不存在、422 格式错误、500 服务器错误。

`/api/chat` 响应 `data` 额外字段：`thread_id`、`checkpointed`、`agent_enabled`、`history_turns`、`confidence`、`stop_reason`、`agent_trace`、`kb_refs`、`needs_confirmation`、`pending_action`，命中时附带 `kb_entry_id`/`question`/`category`，建单时附带 `ticket_no`/`ticket_id`。

---

## 环境变量（关键项，来自 `backend/app/config.py`）

| 变量                            | 默认值                                                        | 说明                    |
| ----------------------------- | ---------------------------------------------------------- | --------------------- |
| `DATABASE_URL`                | `postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/opswarden` | 同时用于 SQLAlchemy 与 checkpointer |
| `SECRET_KEY`                  | `CHANGE_ME_USE_RANDOM_STRING`                               | JWT 签名密钥               |
| `ALGORITHM`                   | `HS256`                                                     | JWT 算法                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480`（8 小时）                                                  | Token 有效期              |
| `DEEPSEEK_API_KEY`            | `local`                                                     | 本地部署通常不校验              |
| `DEEPSEEK_BASE_URL`           | `http://localhost:11434/v1`                                 | OpenAI 兼容接口（Ollama/vLLM） |
| `DEEPSEEK_MODEL`              | `deepseek-r1`                                               | 模型名                   |
| `DEEPSEEK_TEMPERATURE`        | `0.1`                                                       | Agent 决策用 0（在 llm.py 内固定）|
| `DEEPSEEK_MAX_TOKENS`         | `800`                                                       | 决策输出 700              |
| `DEEPSEEK_TIMEOUT`            | `30.0`                                                      | 秒                     |
| `EMBEDDING_MODEL`             | `BAAI/bge-small-zh-v1.5`                                    | 512 维                  |
| `EMBEDDING_DEVICE`            | `cpu`                                                       |                       |
| `RAG_SCORE_THRESHOLD`         | `0.65`                                                      | 低于此值视为未命中（旧值 0.4 已废弃）  |
| `RAG_TOP_K`                   | `3`                                                         | L2 精排返回条数             |
| `RAG_ANCHOR_TOP_K`            | `8`                                                         | L1 锚点召回数              |
| `ANCHOR_QUANT_EPSILON`        | `0.02`                                                      | 锚点量化步长               |

Docker Compose 另有 `POSTGRES_PASSWORD`、`POSTGRES_IMAGE`、`DOCKERHUB_*_IMAGE` 等变量；容器内 `HF_HUB_OFFLINE=1`。

---

## 常见问题

**知识库条目检索不到：** 检查 `kb_entries.embedding` 是否为 NULL，或 `kb_anchors` 是否缺失。模型下载失败多因 `CURL_CA_BUNDLE` 指向无效路径，`main.py` 导入前已自动清除该变量；容器内需保证 `hf_cache` 卷已挂载且模型已预置。

**`checkpointed=false`：** checkpointer 连接池或 `PostgresSaver.setup()` 初始化失败（启动日志会 warning），此时自动回退单轮 `chat_pipeline`，多轮记忆不可用但问答仍可用。

**默认管理员账号：** `admin`，`init.sql` 中密码字段为占位符 `CHANGE_ME_REPLACE_WITH_BCRYPT_HASH`，需自行用 bcrypt 生成哈希替换后再登录（README 里的 `admin123` 已过期）。

**登录/注册报错「请求数据格式错误」：** 后端未重启，旧进程仍在跑旧代码。

---

## 已知遗留项

- `backend/app/graphs/chat_workflow.py`：早期单节点图，当前无引用，与 `agent/graph.py` 功能重复。
- `backend/app/api/chat.py.backup`：过渡期残留备份，引用了已删除的 `app.services.llm_cache_service`。
- `docs/backend.md`：停留在 MySQL 时代，表清单/路由清单/结构树均过时。
- `requirements.txt` 中的 matplotlib/scipy/rank-bm25/hnswlib/scikit-learn 属 RAG 范式对比实验依赖，生产代码未 import（仅 `rag/eval_engine.py` 用 numpy）。
