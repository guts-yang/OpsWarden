# OpsWarden 后端技术说明

> 面向开发者的后端模块、数据库与 API 参考。完整架构见 [TECHNICAL.md](TECHNICAL.md)。

## 技术栈

| 组件 | 选型 |
| --- | --- |
| 语言 / 框架 | Python 3.11、FastAPI 0.115、Uvicorn 0.30 |
| ORM | SQLAlchemy 2.0 + psycopg3 |
| 数据库 | PostgreSQL 16 + pgvector |
| 认证 | JWT（python-jose + passlib/bcrypt） |
| AI 生成 | Ollama 本地 API（OpenAI 兼容 `/v1/chat/completions`） |
| Embedding | sentence-transformers，`BAAI/bge-small-zh-v1.5`（512 维） |
| 对话编排 | LangGraph + langgraph-checkpoint-postgres |

---

## 快速启动

```bash
# 1. 环境
cp .env.example .env
# 编辑 DATABASE_URL、SECRET_KEY、OLLAMA_BASE_URL 等

# 2. 数据库
createdb -U postgres opswarden
psql -U postgres -d opswarden -f init.sql

# 3. Ollama
ollama pull qwen2.5:1.5b

# 4. 依赖与启动
pip install -r requirements.txt
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API 文档：<http://localhost:8000/docs>

---

## 模块划分

```
backend/app/
├── main.py              # 路由注册、启动钩子（FAQ、checkpointer、agent 表）
├── config.py            # pydantic-settings，读取根目录 .env
├── database.py          # Engine、SessionLocal、pgvector 扩展初始化
├── api/
│   ├── auth.py          # POST /api/auth/login
│   ├── account.py       # 账号 CRUD（admin）
│   ├── ticket.py        # 工单全流程 + 知识库回写
│   ├── knowledge.py     # 知识库 CRUD + 按 doc 删除
│   ├── analytics.py     # 仪表盘统计
│   └── chat.py          # POST /api/chat（Agent + 兜底管线）
├── agent/               # LangGraph Agent
│   ├── graph.py         # 状态图：决策 → 工具 → 循环/结束
│   ├── llm.py           # Ollama JSON 决策 + heuristic_decision 兜底
│   ├── tools.py         # kb_search、ticket_*、analytics、health
│   ├── policy.py        # 工具权限与 ticket_create 确认策略
│   ├── prompts.py       # 系统提示词与 AVAILABLE_TOOLS
│   ├── state.py         # AgentState 类型
│   └── trace.py         # agent_runs / agent_tool_calls 审计
├── rag/
│   ├── embedder.py      # BGE 编码（query 带 instruction 前缀）
│   ├── quantizer.py     # 网格量化 ε，生成 quant_key
│   ├── retriever.py     # 双阶段检索、ingest_kb_entry、prune_anchor
│   ├── llm.py           # Ollama 生成（命中 KB / 通用回复）
│   ├── faq_loader.py    # 启动时从 Markdown 导入 FAQ
│   └── chat_pipeline.py # Agent 不可用时的单轮 RAG 兜底
├── middleware/
│   ├── auth.py          # JWT 解析、require_admin / require_operator
│   ├── exception.py     # 统一异常 → {code, message, data}
│   └── logging.py       # 请求日志
├── models/              # SQLAlchemy ORM
├── schemas/             # Pydantic 请求/响应
├── checkpointer/        # LangGraph Postgres checkpoint 连接池
└── utils/               # security、response、employee_id
```

---

## 数据库设计

### ENUM 类型

`account_role`（admin/operator/user）、`account_status`（active/frozen）、`ticket_source`、`ticket_status`、`ticket_priority`、`kb_source`

### accounts 账号表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT IDENTITY | 主键 |
| employee_id | VARCHAR(32) UNIQUE | 工号 |
| username | VARCHAR(64) UNIQUE | 登录名 |
| password_hash | VARCHAR(256) | bcrypt |
| name | VARCHAR(64) | 姓名 |
| department | VARCHAR(128) | 部门 |
| role | account_role | 角色 |
| status | account_status | active / frozen |
| last_login_at | TIMESTAMPTZ | 最后登录 |

### tickets / ticket_logs

工单主表含 `ticket_no`、`source`、`status`、`priority`、`solution`、`is_written_back` 等；`ticket_logs` 记录操作审计（CASCADE 删除）。

### kb_anchors（L1）

| 字段 | 说明 |
| --- | --- |
| quant_key | 量化向量唯一键 |
| anchor_vec | vector(512)，**IVFFlat cosine 索引** |

### kb_entries（L2）

| 字段 | 说明 |
| --- | --- |
| question / solution | 正文 |
| doc_id / page_index | 页级索引，支持按文档精确删除 |
| anchor_id | 外键 → kb_anchors |
| embedding | vector(512)，**仅精排，无 ANN 索引** |
| match_score | Q-S 联合 embedding 自检分 |
| source | manual / ticket_writeback |

### agent_runs / agent_tool_calls

Agent 每次 `/api/chat` 调用写入 `agent_runs`；工具执行明细写入 `agent_tool_calls`（含 latency_ms、success）。

---

## API 接口

### 认证

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| POST | `/api/auth/login` | 无 |

请求体：`{ "username": "...", "password": "..." }`  
响应 `data` 含 `access_token`、`token_type`、`user`。

### 账号管理

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| GET | `/api/accounts/me` | Bearer |
| GET/POST/PUT | `/api/accounts` … | admin |
| PATCH | `/api/accounts/{id}/freeze` 等 | admin |

### 工单

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| POST | `/api/tickets/auto` | 无（内部/RAG 降级） |
| POST | `/api/tickets/manual` | Bearer |
| GET/PUT | `/api/tickets` … | Bearer |
| POST | `/api/tickets/{id}/resolve` | operator+ |
| POST | `/api/tickets/{id}/close` | operator+ |

解决工单时可勾选写回知识库：自动 `ingest_kb_entry` 并向量化。

### 知识库

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/knowledge/stats` | 统计 |
| GET | `/api/knowledge/quick-prompts` | 快捷问题 |
| CRUD | `/api/knowledge` | 增删改查 |
| DELETE | `/api/knowledge/by-doc` | 按 doc_id（+ page_index）批量删 |

### AI 问答

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/chat` | 见 [TECHNICAL.md §4](TECHNICAL.md#4-ai-问答链路) |

请求体：

```json
{
  "query": "VPN 连不上怎么办？",
  "thread_id": "optional-session-uuid",
  "pending_action": null
}
```

确认建单时，客户端将上一轮返回的 `pending_action` 原样带回，用户回复「确认」类关键词后执行。

### 统计

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| GET | `/api/analytics/summary` | Bearer |

---

## 认证说明

- Header：`Authorization: Bearer <access_token>`
- Token 载荷：`sub`（user id）、`username`、`role`
- 有效期：`ACCESS_TOKEN_EXPIRE_MINUTES`（默认 480 分钟）
- 冻结账号：`get_current_user` 返回 401

### 权限矩阵

| 能力 | user | operator | admin |
| --- | --- | --- | --- |
| AI 问答 | ✓ | ✓ | ✓ |
| 工单/知识库/统计 | | ✓ | ✓ |
| 账号管理 | | | ✓ |
| Agent 工具 ticket_search / analytics | | ✓ | ✓ |

---

## 统一响应格式

```json
{ "code": 200, "message": "success", "data": { } }
```

| code | 含义 |
| --- | --- |
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未认证 / Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 422 | 请求体校验失败 |
| 500 | 服务器错误 |

---

## 跨模块调用约定

### RAG → 工单

- **推荐路径**：Agent `ticket_create` 工具 + 用户确认（`pending_action`）
- **兜底路径**：`run_chat_pipeline` 返回 `needs_confirmation: true`，不自动建单
- **遗留接口**：`POST /api/tickets/auto`（无认证，供内部或脚本调用）

### 工单 → 知识库

`POST /api/tickets/{id}/resolve` 且 `write_to_kb=true` 时，创建 `kb_entries` 并调用 `ingest_kb_entry`。

---

## 默认管理员

- 用户名：`admin`
- 密码：在 `init.sql` 中替换 bcrypt hash 后生效

```bash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('你的密码'))"
```

---

## 日志

`RequestLoggingMiddleware` 记录每条请求的方法、路径、状态码、耗时、客户端 IP。
