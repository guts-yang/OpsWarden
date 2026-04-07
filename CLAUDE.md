# OpsWarden — CLAUDE.md

AI 运维数字员工平台。用户通过 AI 问答处理运维问题，命中知识库则直接给出答案，未命中则自动生成工单。

---

## 项目结构

```
OpsWarden/
├── backend/app/          # FastAPI 后端
│   ├── main.py           # 入口，注册路由/中间件/异常处理
│   ├── config.py         # 配置类 Settings（pydantic-settings，读取 .env）
│   ├── database.py       # SQLAlchemy engine、SessionLocal、get_db()
│   ├── api/              # 路由（auth, account, ticket, analytics, knowledge, chat）
│   ├── models/           # ORM 模型（account, ticket, knowledge）
│   ├── schemas/          # Pydantic 请求/响应 schema
│   ├── middleware/       # auth.py（JWT鉴权）、exception.py、logging.py
│   ├── rag/              # RAG 核心（embedder, retriever, llm, faq_loader）
│   └── utils/            # security.py（bcrypt/JWT）、response.py（统一响应）
├── frontend/src/
│   ├── main.js           # Vue 入口
│   ├── router/index.js   # 路由 + 守卫（requiresAuth）
│   ├── stores/auth.js    # Pinia auth store
│   ├── api/              # axios 封装（client.js + 各模块）
│   ├── views/            # 页面组件
│   ├── layouts/          # MainLayout（Sidebar + Header + RouterView）
│   └── components/       # 基础组件（BaseModal, BaseSlidePanel 等）
├── init.sql              # 数据库初始化（schema + 默认管理员）
├── requirements.txt
├── .env                  # 环境变量（不入库）
└── docker-compose.yml    # PostgreSQL 容器
```

---

## 技术栈

<<<<<<< HEAD

| 层    | 技术                                                            |
| ---- | ------------------------------------------------------------- |
| 后端   | Python 3.11 + FastAPI 0.115 + Uvicorn                         |
| ORM  | SQLAlchemy 2.0，驱动 psycopg3                                    |
| 数据库  | PostgreSQL 16 + pgvector（向量索引，cosine distance）                |
| AI   | DeepSeek API（生成答案）+ BAAI/bge-small-zh-v1.5（embedding，512 维）   |
| 前端   | Vue 3 + Vite 6 + Pinia + Vue Router 4 + TailwindCSS 3（MD3 色板） |
| HTTP | Axios，响应拦截器解包 `{code, message, data}` 信封                      |

=======
| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 + FastAPI 0.115 + Uvicorn |
| ORM | SQLAlchemy 2.0，驱动 psycopg3 |
| 数据库 | PostgreSQL 16 + pgvector（向量索引，cosine distance） |
| AI | DeepSeek API（生成答案）+ BAAI/bge-small-zh-v1.5（embedding，512 维） |
| 前端 | Vue 3 + Vite 6 + Pinia + Vue Router 4 + TailwindCSS 3（MD3 色板） |
| HTTP | Axios，响应拦截器解包 `{code, message, data}` 信封 |
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285

---

## 启动方式

```bash
# 数据库（首次）
docker compose up -d
psql -U postgres -d opswarden -f init.sql

# 后端（conda 环境内）
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev        # 开发（http://localhost:5173）
npm run build      # 生产构建 → dist/
```

Vite 开发代理：`/api` → `http://localhost:8000`（无路径重写）。

---

## 核心流程

### AI 问答（RAG）

```
POST /api/chat {query}
  → embed_query()          # BGE 查询向量（加 instruction 前缀）
  → pgvector cosine search # score = 1 - distance，score ≥ 0.4 视为命中
  → [命中] generate_answer(DeepSeek) 或 fallback 直接返回 solution
  → [未命中] 自动创建工单，返回 ticket_no
```

### 知识库条目创建

```
POST /api/knowledge {question, solution, ...}
  → 写入 kb_entries（embedding = NULL）
  → add_entry() 生成 embedding，UPDATE kb_entries SET embedding = vec
  → 失败时 message 返回警告，embedding = NULL，该条目对 RAG 不可见
```

**注意：** embedding 依赖 BAAI/bge-small-zh-v1.5 模型（首次启动自动从 HuggingFace 下载）。`CURL_CA_BUNDLE` 环境变量若指向无效路径会导致下载失败；`main.py` 启动时已自动清除该变量。

### 认证

- JWT（HS256），存于 localStorage（键：`ow_token`, `ow_user`）
- Axios 请求拦截器自动注入 `Authorization: Bearer {token}`
- 401 响应触发自动登出并跳转 `/login`
- 角色：`admin` > `operator` > `user`

---

## API 路由概览

<<<<<<< HEAD

| 路由前缀             | 主要端点                                                      |
| ---------------- | --------------------------------------------------------- |
| `/api/auth`      | `POST /login`，`POST /register`                            |
| `/api/accounts`  | CRUD，`/me`，`/freeze`，`/unfreeze`，`/reset-password`（admin） |
| `/api/tickets`   | `POST /auto`（AI 自动），`/manual`（手动），详情/日志/解决/关闭             |
| `/api/knowledge` | CRUD，`GET /stats`                                         |
| `/api/chat`      | `POST /`（RAG 问答）                                          |
| `/api/analytics` | `GET /summary`（仪表盘统计）                                     |

=======
| 路由前缀 | 主要端点 |
|----------|---------|
| `/api/auth` | `POST /login`，`POST /register` |
| `/api/accounts` | CRUD，`/me`，`/freeze`，`/unfreeze`，`/reset-password`（admin） |
| `/api/tickets` | `POST /auto`（AI 自动），`/manual`（手动），详情/日志/解决/关闭 |
| `/api/knowledge` | CRUD，`GET /stats` |
| `/api/chat` | `POST /`（RAG 问答） |
| `/api/analytics` | `GET /summary`（仪表盘统计） |
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285

---

## 数据模型关键字段

**Account**：`employee_id`（NOT NULL UNIQUE，自注册时格式 `REG_{timestamp_ms}`）、`role`（admin/operator/user）、`status`（active/frozen）

**Ticket**：`ticket_no`（格式 `T-YYYYMMDD-NNN`）、`source`（ai_auto/manual/feishu）、`status`（pending/processing/resolved/closed）、`is_written_back`（是否已回写知识库）

**KBEntry**：`embedding`（pgvector 512维，NULL 表示未建索引，RAG 不可见）、`source`（manual/ticket_writeback）、`match_score`（历史匹配得分）

---

## 统一响应格式

所有接口统一返回：

```json
{ "code": 200, "message": "...", "data": {...} }
```

错误码：400 参数错误、401 未认证、403 权限不足、404 资源不存在、422 格式错误、500 服务器错误。

---

## 环境变量（关键项）

<<<<<<< HEAD

| 变量                            | 说明                          |
| ----------------------------- | --------------------------- |
| `DATABASE_URL`                | PostgreSQL 连接串，psycopg3 格式  |
| `DEEPSEEK_API_KEY`            | DeepSeek API 密钥，AI 回答必需     |
| `EMBEDDING_MODEL`             | 默认 `BAAI/bge-small-zh-v1.5` |
| `RAG_SCORE_THRESHOLD`         | 默认 `0.4`，低于此值触发工单           |
| `RAG_TOP_K`                   | 默认 `3`，返回最相似条数              |
| `SECRET_KEY`                  | JWT 签名密钥                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 默认 `480`（8小时）               |

=======
| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | PostgreSQL 连接串，psycopg3 格式 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥，AI 回答必需 |
| `EMBEDDING_MODEL` | 默认 `BAAI/bge-small-zh-v1.5` |
| `RAG_SCORE_THRESHOLD` | 默认 `0.4`，低于此值触发工单 |
| `RAG_TOP_K` | 默认 `3`，返回最相似条数 |
| `SECRET_KEY` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 默认 `480`（8小时） |
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285

---

## 常见问题

**知识库条目 AI 检索不到：** 检查 `kb_entries.embedding` 是否为 NULL，原因通常是 `CURL_CA_BUNDLE` 环境变量指向无效路径导致模型下载失败。`main.py` 启动时已自动清除，重启后端即可解决新增条目问题；存量 NULL 条目需手动补充 embedding。

**登录/注册报错「请求数据格式错误」：** 后端未重启，旧进程仍在运行旧代码。确认 uvicorn 已使用新代码启动。

<<<<<<< HEAD
**默认管理员账号：** username `admin`，password `admin123`（仅开发环境，生产须修改）。
=======
**默认管理员账号：** username `admin`，password `admin123`（仅开发环境，生产须修改）。
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
