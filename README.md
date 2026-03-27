# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于 DeepSeek + RAG + 飞书

---

## 目录

- [项目简介](#项目简介)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [团队分工](#团队分工)
- [开发规范](#开发规范)
- [常用命令](#常用命令)
- [联调说明](#联调说明)
- [FAQ](#faq)

---

## 项目简介

OpsWarden 是一套面向企业运维场景的 AI 数字员工系统，核心功能三条线：

- **AI 问答**：用户在飞书或 Web 提问，RAG 知识库检索 + DeepSeek 生成回答
- **账号管理**：运维账号的增删改查、冻结、重置，后台可视化管理
- **工单系统**：AI 无法回答时自动创建工单，运维人员处理后回写知识库

**技术栈一览**

| 层次 | 技术 |
|---|---|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy |
| 前端 | Vue3 · Element Plus · Vite |
| 大模型 | DeepSeek API（兼容 OpenAI SDK） |
| 知识库 | LangChain · ChromaDB · bge-small-zh-v1.5 |
| 数据库 | MySQL 8.0 |
| 集成 | 飞书开放平台 Webhook |
| 部署 | Docker Compose · Nginx · 云服务器 |

---

## 快速开始

### 前置要求

- Docker >= 24.0 + Docker Compose >= 2.0
- Python 3.11（本地开发用）
- Node.js 18+（前端开发用）
- Git

### 1. 克隆仓库

```bash
git clone <repo_url>
cd opswarden
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

打开 `.env`，填写以下必填项（搜索 `CHANGE_ME`）：

| 变量 | 说明 | 获取方式 |
|---|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | [platform.deepseek.com](https://platform.deepseek.com) |
| `MYSQL_PASSWORD` | MySQL 用户密码 | 自定义，字母数字组合 |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | 自定义，与上面不同 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 见下方生成命令 |
| `FEISHU_APP_ID` | 飞书应用 ID | 飞书开放平台 → 我的应用 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 同上 |

生成 JWT 密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 启动所有服务

```bash
docker compose up -d
```

首次启动会拉取镜像，约需 3–5 分钟。启动后访问：

| 服务 | 地址 |
|---|---|
| 前端页面 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |

### 4. 初始化知识库

```bash
# 确认后端已正常启动
curl http://localhost:8000/health

# 导入预置 FAQ（100条）
docker compose exec backend python scripts/init_faq.py
```

### 5. 验证安装

```bash
# 测试 RAG 问答
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "账号冻结了怎么处理？"}'
```

返回 `has_knowledge: true` 且 `answer` 有内容即为成功。

---

## 目录结构

```
opswarden/
├── backend/                  # FastAPI 后端
│   ├── api/                  # 路由层
│   │   ├── rag_router.py     # 知识库接口
│   │   ├── account_router.py # 账号管理接口
│   │   ├── ticket_router.py  # 工单接口
│   │   └── feishu_router.py  # 飞书 Webhook
│   ├── rag/                  # AI 核心模块（成员 A）
│   │   ├── embeddings.py     # Embedding 模型封装
│   │   ├── knowledge_base.py # FAQ 录入与向量化
│   │   ├── retriever.py      # RAG 检索 + DeepSeek 问答
│   │   ├── knowledge_updater.py # 工单知识回写
│   │   ├── intent.py         # 意图识别
│   │   └── cache.py          # 问答缓存
│   ├── models/               # 数据库模型（成员 B）
│   │   ├── user.py
│   │   └── ticket.py
│   ├── feishu/               # 飞书集成（成员 D）
│   │   └── bot.py
│   ├── config/
│   │   └── settings.py       # 环境变量读取
│   ├── main.py               # FastAPI 入口
│   └── requirements.txt
├── frontend/                 # Vue3 前端（成员 C）
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用组件
│   │   └── api/              # 接口封装
│   └── package.json
├── scripts/                  # 工具脚本
│   ├── init_faq.py           # 知识库初始化
│   ├── tune_threshold.py     # RAG 阈值调优
│   └── stress_test.py        # 压测脚本
├── nginx/
│   └── default.conf          # Nginx 配置
├── chroma_db/                # ChromaDB 数据（Git 忽略）
├── logs/                     # 日志目录（Git 忽略）
├── docker-compose.yml
├── .env.example              # 环境变量模板
└── README.md
```

---

## 团队分工

| 成员 | 负责模块 | 主要文件 |
|---|---|---|
| **A** | AI 核心 / RAG / DeepSeek | `backend/rag/` · `scripts/` |
| **B** | 后端业务 / 账号 / 工单 / 数据库 | `backend/models/` · `backend/api/account_router.py` · `backend/api/ticket_router.py` |
| **C** | 前端全部页面 | `frontend/src/` |
| **D** | 飞书集成 / Docker / 云服务器 | `backend/feishu/` · `docker-compose.yml` · `nginx/` |

**跨成员依赖关系（需提前沟通接口）：**

- A → B：工单自动创建接口（RAG 无答案时调用 B 的 `POST /tickets`）
- A → D：问答结果通过 D 的飞书 Bot 推送给用户
- B → A：工单关闭时调用 A 的 `POST /rag/writeback`
- C → A/B：前端调用所有后端接口，需 A/B 先完成接口文档

---

## 开发规范

### 分支规范

```
main          ← 稳定版本，只接受 PR 合入
dev           ← 日常联调分支
feat/A-rag    ← 成员 A 功能分支，格式：feat/成员-功能名
fix/B-ticket  ← Bug 修复分支
```

**流程：** 在自己的 `feat/` 分支开发 → PR 合入 `dev` → 联调通过后合入 `main`

### Commit 规范

```
feat: 添加 RAG 相似度阈值调优脚本
fix:  修复账号冻结后无法解冻的问题
docs: 更新 README 快速开始章节
test: 添加意图识别单元测试
chore: 更新 docker-compose MySQL 配置
```

### 接口规范

- 所有接口统一前缀 `/api/v1`
- 响应格式统一：`{"status": "ok"|"error", "data": ..., "message": ...}`
- 错误码：400 参数错误 · 401 未登录 · 403 无权限 · 404 不存在 · 500 服务器错误
- 新增接口在 `http://localhost:8000/docs` 的 Swagger 中验证后再通知前端联调

### Python 规范

- 所有函数加类型注解和 docstring
- 使用 `python-dotenv` 读取环境变量，禁止硬编码密钥
- 异常统一用 `HTTPException`，不要裸露 `Exception`

---

## 常用命令

### Docker 操作

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看后端实时日志
docker compose logs -f backend

# 重启单个服务（改了代码后）
docker compose restart backend

# 完全重建（修改了 Dockerfile 或依赖）
docker compose up -d --build backend

# 停止并清理（保留数据）
docker compose down

# 停止并清理所有数据（慎用）
docker compose down -v
```

### 后端本地开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 本地启动（热重载）
uvicorn main:app --reload --port 8000

# 运行测试
pytest tests/ -v
```

### 前端本地开发

```bash
cd frontend

# 安装依赖
npm install

# 本地启动（热重载，代理到后端 8000）
npm run dev

# 构建生产版本
npm run build
```

### 知识库操作

```bash
# 初始化 / 重新导入 FAQ
docker compose exec backend python scripts/init_faq.py

# RAG 阈值调优
docker compose exec backend python scripts/tune_threshold.py

# 压力测试
docker compose exec backend python scripts/stress_test.py --url http://localhost:8000
```

---

## 联调说明

### 第2周联调检查清单

在合并到 `dev` 分支前，确认以下接口均可正常调用：

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. RAG 问答（A 完成后验证）
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question": "VPN连接失败怎么办"}'

# 3. 账号创建（B 完成后验证）
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"emp_id":"EMP0001","name":"张三","department":"技术运维"}'

# 4. 飞书 Webhook 验证（D 完成后验证）
curl -X POST http://localhost:8000/api/v1/feishu/webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test123"}'
```

### 演示场景验收标准

| 场景 | 验收标准 |
|---|---|
| 飞书智能问答 | 发送"账号冻结了"，3秒内收到飞书回复，`has_knowledge=true` |
| 账号管理 | 后台创建账号后，前台搜索立即可见 |
| 工单闭环 | 问知识库没有的问题 → 工单生成 → 处理 → 再问同一问题有答案 |

---

## FAQ

**Q: 首次启动后 Embedding 模型下载很慢？**
A: 模型约 100MB，国内网络可能较慢。可手动下载后放入 Docker Volume，或在 `.env` 中配置 HuggingFace 镜像：
```bash
HF_ENDPOINT=https://hf-mirror.com
```

**Q: DeepSeek API 返回 429 限流错误？**
A: 降低并发请求数，或在 `.env` 中开启缓存：`RAG_CACHE_TTL=3600`。测试阶段建议逐个发送请求，不要并发。

**Q: ChromaDB 数据重启后丢失？**
A: 检查 `docker-compose.yml` 中 `chroma_data` Volume 是否正确挂载到 `/chroma/chroma`，并确认 `knowledge_base.py` 中每次写入后调用了 `db.persist()`。

**Q: 飞书 Webhook 收不到消息？**
A: 确认云服务器的 80/443 端口已开放，飞书后台配置的 Webhook URL 为公网地址而非 localhost，且签名验证通过。

**Q: MySQL 连接报 `Access denied`？**
A: 检查 `.env` 中 `MYSQL_USER`、`MYSQL_PASSWORD` 与 `DATABASE_URL` 中的用户名密码是否一致，重建容器：`docker compose down -v && docker compose up -d`。

**Q: 前端页面空白或报 CORS 错误？**
A: 检查 `.env` 中 `CORS_ORIGINS` 是否包含前端实际访问地址（含端口号）。

---

## 联系方式

| 角色 | 负责人 | 飞书 |
|---|---|---|
| AI 核心 / RAG | 成员 A | @成员A |
| 后端 / 数据库 | 成员 B | @成员B |
| 前端 | 成员 C | @成员C |
| 部署 / 飞书集成 | 成员 D | @成员D |
| 指导老师 | 黄平 | 13302332400 |

---

*OpsWarden · Ver 1.0 · 课题六：运维数字员工的建设*