# OpsWarden 技术文档

> 版本：1.0 · 最后对齐代码库：OpsWarden 主分支  
> 读者：架构师、后端/前端开发、运维部署人员

---

## 目录

1. [系统概述](#1-系统概述)
2. [总体架构](#2-总体架构)
3. [技术选型](#3-技术选型)
4. [AI 问答链路](#4-ai-问答链路)
5. [RAG 检索引擎](#5-rag-检索引擎)
6. [LangGraph Agent](#6-langgraph-agent)
7. [数据模型](#7-数据模型)
8. [API 与鉴权](#8-api-与鉴权)
9. [前端架构](#9-前端架构)
10. [部署架构](#10-部署架构)
11. [配置参考](#11-配置参考)
12. [自学习闭环](#12-自学习闭环)
13. [运维与排障](#13-运维与排障)
14. [附录](#14-附录)

---

## 1. 系统概述

OpsWarden 是一套面向企业 IT 运维场景的 **AI 数字员工平台**，核心能力：

| 能力 | 说明 |
| --- | --- |
| **智能问答** | 双层 RAG 检索 + Ollama 本地大模型生成；LangGraph Agent 支持多工具编排 |
| **工单管理** | 全生命周期（待处理 → 处理中 → 已解决 → 已关闭），支持 AI 辅助建单 |
| **知识库** | 页级索引（`doc_id` + `page_index`），支持精确删除与工单回写 |
| **账号权限** | 三级角色（user / operator / admin），JWT + 路由/接口双重校验 |
| **自学习** | 工单解决写回知识库 → 向量化建锚点 → 下次同类问题直接命中 |

**设计原则：**

- **本地优先**：Embedding 与 LLM 均在本地运行，无外网 API Key 依赖
- **优雅降级**：Agent、Ollama、checkpoint 任一环节失败均有兜底路径
- **安全建单**：知识库未命中时不静默创建工单，需用户明确确认

---

## 2. 总体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         用户（浏览器 / 移动端）                            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTPS / HTTP
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Vite + Pinia)                                        │
│  Login · Dashboard · Tickets · Knowledge · AiChat                       │
│  JWT in localStorage · /api 代理 → :8000                                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ REST JSON { code, message, data }
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ api/chat     │→ │ agent/graph  │→ │ agent/tools  │→ │ rag/*      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  api/auth · account · ticket · knowledge · analytics                    │
│  middleware: JWT · logging · exception                                   │
└───────┬─────────────────────────────┬───────────────────────────────────┘
        │                             │
        ▼                             ▼
┌───────────────────┐       ┌───────────────────┐
│ PostgreSQL 16     │       │ Ollama            │
│ + pgvector        │       │ qwen2.5:1.5b 等   │
│ kb_anchors        │       │ :11434/v1/chat    │
│ kb_entries        │       └───────────────────┘
│ accounts/tickets  │
│ agent_runs        │       ┌───────────────────┐
│ LangGraph         │◄──────│ BGE Embedding     │
│ checkpoint 表     │       │ bge-small-zh-v1.5 │
└───────────────────┘       └───────────────────┘
```

系统机制示意图见 [`docs/canva.png`](canva.png)。图中标注为 DeepSeek，**当前代码实现已切换为 Ollama**（`OLLAMA_BASE_URL` + `OLLAMA_MODEL`），其余 RAG 与 pgvector 架构一致。

---

## 3. 技术选型

### 3.1 后端

| 组件 | 版本/说明 |
| --- | --- |
| Python | 3.11 |
| FastAPI | 0.115 |
| Uvicorn | 0.30 |
| SQLAlchemy | 2.0 + psycopg3 |
| LangGraph | ≥0.2，Postgres checkpoint |
| sentence-transformers | BGE embedding |
| httpx | 异步调用 Ollama |

### 3.2 数据层

| 组件 | 说明 |
| --- | --- |
| PostgreSQL | 16 |
| pgvector | vector(512)，cosine distance |
| IVFFlat | 仅建在 `kb_anchors.anchor_vec`（lists=50） |

### 3.3 AI 层

| 组件 | 默认配置 |
| --- | --- |
| Embedding | `BAAI/bge-small-zh-v1.5`，512 维，CPU |
| LLM | Ollama `qwen2.5:1.5b`，temperature=0.1 |
| 检索阈值 | `RAG_SCORE_THRESHOLD=0.65`（v3 联合调优） |

### 3.4 前端

| 组件 | 说明 |
| --- | --- |
| Vue 3 + Vite 6 | SPA |
| Pinia | 认证状态 |
| Vue Router 4 | 角色路由守卫 |
| Tailwind CSS 3 | MD3 色板 |
| Axios | 统一响应解包 |

---

## 4. AI 问答链路

入口：`POST /api/chat`（`backend/app/api/chat.py`）

### 4.1 请求与响应

**请求：**

```json
{
  "query": "用户问题",
  "thread_id": "可选-客户端会话ID",
  "pending_action": null
}
```

- `thread_id`：经服务端规范化为 `user-{id}-{clientId}`，用于 LangGraph Postgres checkpoint 多轮隔离
- `pending_action`：上一轮返回的待确认操作（如建单），用户回复「确认」后执行

**响应 `data` 关键字段：**

| 字段 | 说明 |
| --- | --- |
| `answer` | 最终回复文本 |
| `source` | `kb` / `agent` / `fallback` / `error` |
| `thread_id` | 会话 ID |
| `checkpointed` | 是否走 LangGraph checkpoint |
| `agent_enabled` | 是否启用 Agent |
| `needs_confirmation` | 是否需要用户确认下一步 |
| `pending_action` | 待确认的工具调用 |
| `kb_refs` | 命中的知识库条目 |
| `ticket_no` | 建单成功时的工单号 |
| `agent_trace` | 工具调用轨迹 |

### 4.2 处理流程

```
                    POST /api/chat
                          │
          ┌───────────────┴───────────────┐
          │ pending_action + 用户确认/取消？  │
          └───────────────┬───────────────┘
                    是 │ 直接 execute_tool
                       ▼
              create_run (agent_runs 审计)
                       │
                       ▼
         invoke_agent_with_checkpoint (LangGraph)
                       │
         ┌─────────────┴─────────────┐
         │ 成功                       │ 失败 (RuntimeError 等)
         ▼                             ▼
   返回 Agent 结果              run_chat_pipeline (兜底)
                                       │
                               RAG 检索 + Ollama
                               未命中 → needs_confirmation
```

### 4.3 兜底管线（`chat_pipeline.py`）

当 LangGraph / checkpoint 不可用时：

1. `rag_search(query)` 双阶段检索
2. **命中**：`generate_answer()` 调 Ollama，失败则返回 `solution` 原文
3. **未命中**：`generate_general_answer()` 或固定引导语 + `needs_confirmation: true`
4. **不自动建单**——与 Agent 策略一致

---

## 5. RAG 检索引擎

实现：`backend/app/rag/retriever.py`

### 5.1 两阶段检索

| 阶段 | 数据表 | 方法 | 参数 |
| --- | --- | --- | --- |
| **L1 锚点路由** | `kb_anchors` | IVFFlat + cosine distance，取 Top-K | `RAG_ANCHOR_TOP_K=8` |
| **L2 页级精排** | `kb_entries` | 全精度余弦相似度 | `RAG_SCORE_THRESHOLD=0.65` |
| **输出** | — | 按分数降序，取 Top `RAG_TOP_K=3` | |

**分数计算：** L2 阶段 `score = dot(q, e) / (||q|| · ||e||)`，BGE 输出已 L2 归一化时等价于余弦相似度。

### 5.2 向量写入（`ingest_kb_entry`）

1. 分别对 `question`、`solution` 做 embedding
2. 计算 **match_score**（Q-S 余弦相似度，条目质量自检）
3. 联合向量：`joint = normalize((qv + sv) / 2)`
4. 网格量化：`quantize_vector(joint, ANCHOR_QUANT_EPSILON)` → `quant_key`
5. Upsert `kb_anchors`，更新 `kb_entries.anchor_id` 与 `embedding`

### 5.3 精确遗忘

- 单条：`DELETE /api/knowledge/{id}` → 删除条目 → `prune_anchor_if_unused`
- 批量：`DELETE /api/knowledge/by-doc?doc_id=...&page_index=...`
- 无需重建全库向量索引

### 5.4 FAQ 自动导入

启动时 `main.py` → `faq_loader.load_faq_if_empty()`：解析 `backend/knowledge_base/OpsWarden_FAQ.md`，`doc_id=OpsWarden_FAQ`，`page_index` 为条目序号。

可选批量导入：根目录 `import_knowledge.py`（需后端已启动、有效 JWT）。

### 5.5 调优背景

`RAG_SCORE_THRESHOLD` 由 0.4 上调至 **0.65**，显著降低误命中（FPR）。详见：

- [`rag_hyperparam_report_v3_joint.md`](rag_hyperparam_report_v3_joint.md)
- [`rag_hyperparam_report.md`](rag_hyperparam_report.md)

> 本仓库含调优报告文档，**不含** `scripts/rag_hyperparam_eval.py` 等复现脚本。

---

## 6. LangGraph Agent

实现：`backend/app/agent/`

### 6.1 状态图

- 入口：`graph.py` → `invoke_agent_with_checkpoint`
- 决策：`llm.py` → `decide_with_llm`（Ollama JSON mode）或 `heuristic_decision`（规则兜底）
- 执行：`tools.py` → `execute_tool`
- 策略：`policy.py` → 工具权限、`ticket_create` 需确认
- 审计：`trace.py` → `agent_runs` / `agent_tool_calls`
- 最大步数：**5**（`MAX_AGENT_STEPS`）

### 6.2 可用工具

| 工具 | 权限 | 说明 |
| --- | --- | --- |
| `kb_search` | 全部登录用户 | RAG 检索 |
| `ticket_create` | 全部 | **需用户确认** |
| `ticket_get` | 全部 | 按 id / ticket_no 查询 |
| `ticket_search` | operator+ | 关键词/状态/优先级搜索 |
| `analytics_summary` | operator+ | 仪表盘统计 |
| `system_health_check` | 全部 | DB + 向量库健康 |

### 6.3 决策 JSON 格式

Agent 要求 Ollama 返回 JSON：

```json
{
  "type": "tool_call | final_answer | ask_user | confirm_action",
  "tool": "kb_search",
  "args": { "query": "...", "top_k": 3 },
  "answer": "...",
  "confidence": 0.8,
  "pending_action": { }
}
```

`confirm_action` 用于未命中知识库时询问是否建单，前端需将 `pending_action` 在下一轮请求中回传。

### 6.4 Checkpoint

- 驱动：`langgraph-checkpoint-postgres`
- 连接池：`checkpointer/runtime.py`
- `thread_id` 隔离多用户多会话历史

---

## 7. 数据模型

完整 DDL：`init.sql`

### 7.1 实体关系（简图）

```
accounts ──┬── reporter_id ──► tickets ◄── ticket_logs
           └── assignee_id

kb_anchors ◄── anchor_id ── kb_entries

agent_runs ◄── run_id ── agent_tool_calls
```

### 7.2 知识库表要点

**kb_anchors**

| 列 | 类型 | 索引 |
| --- | --- | --- |
| quant_key | VARCHAR(64) UNIQUE | — |
| anchor_vec | vector(512) | IVFFlat (cosine) |

**kb_entries**

| 列 | 说明 |
| --- | --- |
| doc_id / page_index | 文档页级定位 |
| embedding | 精排向量，NULL 则 RAG 不可见 |
| match_score | Q-S 自检分，非检索分 |
| source | manual / ticket_writeback |

### 7.3 工单状态机

```
pending → processing → resolved → closed
```

解决时可 `write_to_kb` 触发知识库回写。

---

## 8. API 与鉴权

### 8.1 路由一览

| 前缀 | 文件 | 职责 |
| --- | --- | --- |
| `/api/auth` | auth.py | 登录 |
| `/api/accounts` | account.py | 账号 CRUD |
| `/api/tickets` | ticket.py | 工单 |
| `/api/knowledge` | knowledge.py | 知识库 |
| `/api/chat` | chat.py | AI 问答 |
| `/api/analytics` | analytics.py | 统计 |
| `/health` | main.py | 健康检查 |

### 8.2 JWT

- 签发：`utils/security.py`，密钥 `SECRET_KEY`
- 校验：`middleware/auth.py`
- 载荷：`sub`（用户 ID）、`username`、`role`
- 前端存储：`localStorage` 键 `ow_token`、`ow_user`

### 8.3 角色与前端路由

| 路由 | admin | operator | user |
| --- | --- | --- | --- |
| `/` Dashboard | ✓ | ✓ | → 重定向 `/chat` |
| `/accounts` | ✓ | ✗ | ✗ |
| `/tickets` | ✓ | ✓ | ✗ |
| `/knowledge` | ✓ | ✓ | ✗ |
| `/chat` | ✓ | ✓ | ✓ |

---

## 9. 前端架构

```
frontend/src/
├── api/client.js       # Axios 实例，401 自动登出
├── stores/auth.js      # Pinia 认证
├── router/index.js     # 路由守卫
├── layouts/MainLayout.vue
├── views/              # 六大页面
├── components/
│   ├── AppSidebar.vue / AppHeader.vue
│   └── AppBottomTabBar.vue   # 移动端底栏
└── utils/
    └── chatSessionStorage.js # 多会话本地持久化
```

### 9.1 AI 问答页（AiChatView）

- 调用 `POST /api/chat`，传递 `thread_id` 维持多轮
- 处理 `needs_confirmation` / `pending_action` 确认建单 UI
- 展示 `agent_trace`、`kb_refs`（若返回）

### 9.2 构建与代理

- 开发：`npm run dev`，端口 5173，`/api` → `localhost:8000`
- 生产：`npm run build` → 项目根 `dist/`
- Docker：nginx 容器，端口 8080，同源 `/api` 反代 backend

---

## 10. 部署架构

### 10.1 Docker Compose 服务

| 服务 | 镜像/构建 | 端口 | 说明 |
| --- | --- | --- | --- |
| postgres | pgvector/pgvector:pg16 | 5432 | 数据持久化 volume |
| backend | backend/Dockerfile | 8000 | hf_cache volume |
| frontend | frontend/Dockerfile + nginx | 8080 | 静态资源 |

### 10.2 注意事项

1. **Ollama 不在 Compose 内**，需宿主机单独部署
2. 容器内访问宿主机 Ollama：`OLLAMA_BASE_URL=http://host.docker.internal:11434`（Linux 需额外配置）
3. `POSTGRES_PASSWORD` 与 `DATABASE_URL` 密码必须一致
4. 首次启动自动执行 `init.sql`（仅空数据卷）

### 10.3 本地开发拓扑

```
localhost:5173 (Vite) ──proxy──► localhost:8000 (FastAPI)
localhost:8000 ──► localhost:5432 (PostgreSQL)
localhost:8000 ──► localhost:11434 (Ollama)
```

---

## 11. 配置参考

与 `backend/app/config.py`、`.env.example` 对齐：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | — | Docker 数据库密码 |
| `DATABASE_URL` | psycopg3 连接串 | 本地或容器 |
| `SECRET_KEY` | 需修改 | JWT 签名 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 480 | Token 有效期 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | **不含** `/v1` |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | 模型名 |
| `OLLAMA_TEMPERATURE` | 0.1 | 生成温度 |
| `OLLAMA_MAX_TOKENS` | 800 | 最大 token |
| `OLLAMA_TIMEOUT` | 30（.env）/ 60（代码默认） | 秒 |
| `EMBEDDING_MODEL` | BAAI/bge-small-zh-v1.5 | — |
| `EMBEDDING_DEVICE` | cpu | — |
| `RAG_SCORE_THRESHOLD` | 0.65 | L2 命中阈值 |
| `RAG_TOP_K` | 3 | 返回条数 |
| `RAG_ANCHOR_TOP_K` | 8 | L1 锚点数 |
| `ANCHOR_QUANT_EPSILON` | 0.02 | 量化步长 ε |

---

## 12. 自学习闭环

```
① 用户提问
      │
      ▼
② RAG 未命中（score < 0.65）
      │
      ▼
③ 用户确认 → ticket_create
      │
      ▼
④ 运维处理工单 → resolve + write_to_kb
      │
      ▼
⑤ ingest_kb_entry（向量化 + 建锚点）
      │
      ▼
⑥ 下次同类问题 L2 命中 → Ollama 生成答案
```

**精确反学习：** 按 `doc_id` / `page_index` 删除条目，孤立锚点自动 prune，无需全量重建索引。

---

## 13. 运维与排障

### 13.1 健康检查

```bash
curl http://localhost:8000/health
```

期望：`database: connected`，`vector_store: ok`，`vector_docs` ≥ 0

### 13.2 常见问题

| 现象 | 排查 |
| --- | --- |
| AI 无生成，仅返回 KB 原文 | `ollama list`；检查 `OLLAMA_BASE_URL` / `OLLAMA_MODEL` |
| vector_store: error | `\dx` 确认 pgvector；是否执行 init.sql |
| 知识库检索为空 | `kb_entries.embedding IS NULL`；重启后端重试写入 |
| Agent 不 checkpoint | 检查 checkpointer 连接池日志；回退 `checkpointed: false` 仍可用 |
| admin 无法登录 | init.sql 密码 hash 是否为占位符 |
| Docker 内 AI 失败 | Ollama 地址是否可从容器访问 |

### 13.3 实用脚本

| 脚本 | 用途 |
| --- | --- |
| `scripts/docker_verify_log.py` | Compose 校验与日志 |
| `scripts/migrate_kb_anchors.sql` | 旧库升级锚点架构 |
| `scripts/reset_kb.py` | 重置知识库 |
| `scripts/recompute_match_score.py` | 重算 match_score |
| `import_knowledge.py` | API 批量导入 FAQ |

### 13.4 日志

- HTTP 请求：`middleware/logging.py`
- RAG 分数分布：`retriever.search` INFO 级别 top-5 scores
- Agent 决策失败：`agent/llm.py` WARNING → 回退 heuristic

---

## 14. 附录

### 14.1 相关文档

| 文档 | 内容 |
| --- | --- |
| [README.md](../README.md) | 快速开始、FAQ |
| [backend.md](backend.md) | 后端 API 与模块速查 |
| [API_TESTING.md](API_TESTING.md) | 接口测试 |
| [CLAUDE.md](../CLAUDE.md) | AI 协作者速览 |
| [rag_hyperparam_report_v3_joint.md](rag_hyperparam_report_v3_joint.md) | RAG 阈值调优 |

### 14.2 灵感来源

- 论文：[Fast Exact Unlearning for In-Context Learning Data for LLMs](https://arxiv.org/abs/2402.00751)
- 开源：[PageIndex](https://github.com/VectifyAI/PageIndex)

### 14.3 版本说明

| 项 | 说明 |
| --- | --- |
| API 版本 | 1.0.0（`FastAPI title`） |
| 架构图 | `docs/canva.png` 中 LLM 标注为 DeepSeek，实现已迁移 Ollama |
| 未接入模块 | `agent/mllm.py`（遗留）、`models/llm_cache.py`（无表、未接线） |

---

*OpsWarden · 课题六：运维数字员工的建设*
