# OpsWarden

> AI-Powered Operations Digital Employee Platform
> 运维数字员工系统 · 基于 DeepSeek + FastAPI + MySQL

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Auth-000000?logo=jsonwebtokens&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 目录

- [项目简介](#项目简介)
- [快速开始（本地，无需 Docker）](#快速开始本地无需-docker)
- [Docker 部署](#docker-部署)
- [目录结构](#目录结构)
- [API 接口](#api-接口)
- [团队分工](#团队分工)
- [开发规范](#开发规范)
- [FAQ](#faq)

---

## 项目简介

OpsWarden 是一套面向企业运维场景的 AI 数字员工系统，核心功能三条线：

- **AI 问答**：用户在 Web 提问，自动创建工单并由运维人员跟进处理
- **账号管理**：运维账号的增删改查、冻结、重置密码，后台可视化管理
- **工单系统**：工单全生命周期管理（待处理 → 处理中 → 已解决 → 已关闭）

**技术栈**

| 层次 | 技术 | 版本 |
|---|---|---|
| 后端框架 | FastAPI + Uvicorn | 0.115 / 0.30 |
| ORM | SQLAlchemy + PyMySQL | 2.0 / 1.1 |
| 认证 | JWT (python-jose + passlib) | HS256 |
| 前端 | 原生 HTML/JS + Tailwind CSS CDN | 3.x |
| 数据库 | MySQL | 8.0 |
| 运行时 | Python | 3.11 |

---

## 快速开始（本地，无需 Docker）

适合本机已有 MySQL 的开发环境，无需安装 Docker。

### 前置要求

- Python 3.11+
- MySQL 8.0（本地已运行）
- Git

### 1. 克隆仓库

```bash
git clone https://github.com/guts-yang/OpsWarden.git
cd OpsWarden
```

### 2. 初始化数据库

以 root 身份登录 MySQL，执行初始化脚本：

```bash
mysql -u root -p < init.sql
```

`init.sql` 会自动完成以下操作：
- 创建数据库 `opswarden`
- 创建用户 `ops`（密码 `ops123456`）并授权
- 建表：`accounts`、`tickets`、`ticket_logs`
- 插入默认管理员账号：用户名 `admin`，密码 `admin123`

> **注意**：若 MySQL 仅允许 `localhost` 连接，脚本末尾的 `GRANT` 语句需同时包含 `'ops'@'localhost'`。可手动执行：
> ```sql
> CREATE USER IF NOT EXISTS 'ops'@'localhost' IDENTIFIED BY 'ops123456';
> GRANT ALL PRIVILEGES ON opswarden.* TO 'ops'@'localhost';
> FLUSH PRIVILEGES;
> ```

### 3. 启动后端

```bash
cd backend
pip install -r ../requirements.txt
uvicorn app.main:app --reload --port 8000
```

验证：访问 [http://localhost:8000/health](http://localhost:8000/health)，应返回 `"database": "connected"`。

API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

### 4. 启动前端

新开一个终端，在项目根目录执行：

```bash
python -m http.server 3000 -d frontend/pages
```

浏览器打开 [http://localhost:3000/login.html](http://localhost:3000/login.html)，使用 `admin` / `admin123` 登录。

### 5. 配置环境变量（可选）

默认配置已可直接运行。如需修改数据库连接或密钥：

```bash
cp .env.example .env
# 编辑 .env，填写需要修改的值
```

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://ops:ops123456@localhost:3306/opswarden` | 数据库连接串 |
| `SECRET_KEY` | `ops-warden-secret-key` | JWT 签名密钥（生产环境请修改） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Token 有效期（分钟） |
| `DEEPSEEK_API_KEY` | _(空)_ | DeepSeek API 密钥（AI 功能扩展时使用） |

生成强密钥：

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Docker 部署

如果本地未安装 MySQL，可使用 Docker Compose 一键启动全部服务。

> **注意**：若本机 3306 端口已被占用（本地 MySQL 正在运行），请先停止本地 MySQL，或修改 `docker-compose.yml` 中的端口映射（如改为 `3307:3306`），同时更新 `.env` 中的 `DATABASE_URL`。

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

启动后按照[上方步骤 3–4](#3-启动后端) 启动后端和前端。

---

## 目录结构

```
OpsWarden/
├── backend/
│   └── app/
│       ├── api/                # 路由层
│       │   ├── auth.py         # 登录认证
│       │   ├── account.py      # 账号管理 CRUD
│       │   └── ticket.py       # 工单管理
│       ├── middleware/         # 中间件
│       │   ├── auth.py         # JWT 鉴权
│       │   ├── exception.py    # 统一异常处理
│       │   └── logging.py      # 请求日志
│       ├── models/             # SQLAlchemy ORM 模型
│       │   ├── account.py
│       │   └── ticket.py
│       ├── schemas/            # Pydantic 请求/响应模型
│       │   ├── account.py
│       │   └── ticket.py
│       ├── utils/
│       │   ├── response.py     # 统一响应格式
│       │   └── security.py     # 密码哈希 / JWT 工具
│       ├── config.py           # 环境变量配置
│       ├── database.py         # 数据库连接
│       └── main.py             # FastAPI 入口
├── frontend/
│   └── pages/
│       ├── api.js              # 共享 API 客户端（所有页面引用）
│       ├── login.html          # 登录页
│       ├── dashboard.html      # 仪表盘
│       ├── accounts.html       # 账号管理
│       ├── tickets.html        # 工单管理
│       ├── ai_chat.html        # AI 对话 / 提交工单
│       └── knowledge_base.html # 知识库
├── docs/
│   ├── API_TESTING.md          # API 测试文档
│   ├── backend.md              # 后端设计文档
│   └── screenshots/            # 页面截图
├── backend/
│   └── knowledge_base/
│       └── OpsWarden_FAQ.md    # 知识库 FAQ 内容
├── init.sql                    # 数据库初始化脚本
├── requirements.txt            # Python 依赖
├── docker-compose.yml          # Docker 编排（仅 MySQL）
├── .env.example                # 环境变量模板
└── README.md
```

---

## API 接口

所有接口基础路径：`http://localhost:8000`

| 接口 | 方法 | 路径 | 认证 |
|---|---|---|---|
| 登录 | POST | `/api/auth/login` | 无 |
| 账号列表 | GET | `/api/accounts` | Bearer |
| 创建账号 | POST | `/api/accounts` | Bearer (admin) |
| 更新账号 | PUT | `/api/accounts/{id}` | Bearer (admin) |
| 冻结账号 | PATCH | `/api/accounts/{id}/freeze` | Bearer (admin) |
| 解冻账号 | PATCH | `/api/accounts/{id}/unfreeze` | Bearer (admin) |
| 重置密码 | PATCH | `/api/accounts/{id}/reset-password` | Bearer (admin) |
| 工单列表 | GET | `/api/tickets` | Bearer |
| 工单详情 | GET | `/api/tickets/{id}` | Bearer |
| 工单日志 | GET | `/api/tickets/{id}/logs` | Bearer |
| 更新工单 | PUT | `/api/tickets/{id}` | Bearer (operator+) |
| 解决工单 | POST | `/api/tickets/{id}/resolve` | Bearer (operator+) |
| 关闭工单 | POST | `/api/tickets/{id}/close` | Bearer (operator+) |
| 创建工单（自动） | POST | `/api/tickets/auto` | 无 |

完整接口文档：[http://localhost:8000/docs](http://localhost:8000/docs)（Swagger UI）

---

## 团队分工

| 成员 | 负责模块 | 主要文件 |
|---|---|---|
| **A** | AI 核心 / RAG / DeepSeek | `backend/rag/` · `scripts/` |
| **B** | 后端业务 / 账号 / 工单 / 数据库 | `backend/app/api/` · `backend/app/models/` · `init.sql` |
| **C** | 前端全部页面 | `frontend/pages/` |
| **D** | 飞书集成 / Docker / 云服务器 | `docker-compose.yml` · 飞书 Webhook |

---

## 开发规范

### 分支规范

```
main          ← 稳定版本，只接受 PR 合入
dev           ← 日常联调分支
feat/A-rag    ← 成员 A 功能分支，格式：feat/成员-功能名
fix/B-ticket  ← Bug 修复分支
```

### Commit 规范

```
feat: 添加账号冻结功能
fix:  修复 CORS 跨域问题
docs: 更新 README 本地部署章节
test: 添加工单状态流转测试
chore: 更新依赖版本
```

### 接口规范

- 响应格式统一：`{"code": 200, "message": "ok", "data": ...}`
- 错误码：`400` 参数错误 · `401` 未登录 · `403` 无权限 · `404` 不存在 · `500` 服务器错误
- 新增接口在 Swagger (`/docs`) 验证后再通知前端联调

---

## FAQ

**Q: 后端启动报 `Access denied for user 'ops'@'localhost'`？**

A: 说明数据库未初始化或 `ops` 用户缺少 `@localhost` 授权。执行：
```sql
CREATE USER IF NOT EXISTS 'ops'@'localhost' IDENTIFIED BY 'ops123456';
GRANT ALL PRIVILEGES ON opswarden.* TO 'ops'@'localhost';
FLUSH PRIVILEGES;
```

**Q: 浏览器显示"无法连接到后端服务"？**

A: 确认后端已在 8000 端口运行（`curl http://localhost:8000/health`）。如果后端正常但仍报错，检查 CORS 配置——`allow_origins=["*"]` 与 `allow_credentials=True` 不能同时使用。

**Q: Docker 启动报端口 3306 冲突？**

A: 本机 MySQL 已占用 3306 端口。选择其一：
- 停止本机 MySQL，再运行 `docker compose up -d`
- 改用[本地部署方式](#快速开始本地无需-docker)，直接在本机 MySQL 上初始化数据库

**Q: 登录提示用户名或密码错误？**

A: 默认账号 `admin` / `admin123`。确认 `init.sql` 已成功执行（检查 `accounts` 表是否有数据）。

**Q: 前端页面跳转到 login 但已登录？**

A: 清除浏览器 localStorage 后重新登录（F12 → Application → Local Storage → 清空）。

---

## 联系方式

| 角色 | 负责人 | 联系 |
|---|---|---|
| AI 核心 / RAG | 成员 A | @成员A |
| 后端 / 数据库 | 成员 B | @成员B |
| 前端 | 成员 C | @成员C |
| 部署 / 飞书集成 | 成员 D | @成员D |
| 指导老师 | 黄平 | 13302332400 |

---

*OpsWarden · Ver 1.0 · 课题六：运维数字员工的建设*
