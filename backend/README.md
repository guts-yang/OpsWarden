# OpsWarden 后端 - 账号管理 & 工单系统

> 成员 B 负责模块：数据库设计、账号CRUD、JWT鉴权、工单全流程

## 技术栈

- Python 3.10 + FastAPI
- MySQL 8.0 + SQLAlchemy + pymysql
- JWT认证 (python-jose + passlib/bcrypt)
- Docker Compose

## 快速启动

### 1. 启动 MySQL

```bash
cd 项目根目录
docker compose up -d mysql
2. 安装依赖
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际配置
4. 启动后端
uvicorn app.main:app --reload --port 8000
5. 访问API文档
http://localhost:8000/docs

## 数据库设计

### accounts 账号表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | bigint | 主键自增 |
| employee_id | varchar(32) | 工号，唯一 |
| username | varchar(64) | 用户名，唯一 |
| password_hash | varchar(256) | bcrypt加密密码 |
| name | varchar(64) | 姓名 |
| department | varchar(128) | 部门 |
| email | varchar(128) | 邮箱 |
| phone | varchar(20) | 手机号 |
| role | enum | admin/operator/user |
| status | enum | active/frozen |
| last_login_at | datetime | 最后登录时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
### tickets 工单表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | bigint | 主键自增 |
| ticket_no | varchar(32) | 工单编号 T-YYYYMMDD-NNN |
| title | varchar(256) | 标题 |
| description | text | 描述 |
| source | enum | ai_auto/manual/feishu |
| status | enum | pending/processing/resolved/closed |
| priority | enum | low/medium/high/urgent |
| reporter_id | bigint | 报障人ID |
| reporter_name | varchar(64) | 报障人姓名 |
| assignee_id | bigint | 处理人ID |
| solution | text | 解决方案 |
| is_written_back | tinyint | 是否回写知识库 |
| callback_note | text | 回访备注 |
| callback_at | datetime | 回访时间 |
| resolved_at | datetime | 解决时间 |
| closed_at | datetime | 关闭时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
### ticket_logs 工单日志表

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | bigint | 主键自增 |
| ticket_id | bigint | 关联工单ID |
| action | varchar(64) | 操作类型 |
| operator_id | bigint | 操作人ID |
| operator_name | varchar(64) | 操作人姓名 |
| content | text | 操作内容 |
| created_at | datetime | 操作时间 |
## API 接口文档

### 认证

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/auth/login | 用户登录，返回JWT Token | 无 |
### 账号管理

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/accounts | 创建运维账号 | admin |
| GET | /api/accounts | 查询账号列表（支持筛选+分页） | login |
| GET | /api/accounts/{id} | 查询账号详情 | login |
| PUT | /api/accounts/{id} | 修改账号信息 | admin |
| PATCH | /api/accounts/{id}/freeze | 冻结账号 | admin |
| PATCH | /api/accounts/{id}/unfreeze | 解冻账号 | admin |
| PATCH | /api/accounts/{id}/reset-password | 重置密码 | admin |
### 工单管理

| 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- |
| POST | /api/tickets/auto | AI自动生成工单 | 无（内部调用） |
| GET | /api/tickets | 查询工单列表（支持筛选+分页） | login |
| GET | /api/tickets/{id} | 查询工单详情 | login |
| GET | /api/tickets/{id}/logs | 查询操作日志 | login |
| PUT | /api/tickets/{id} | 更新工单 | operator |
| POST | /api/tickets/{id}/resolve | 解决工单 | operator |
| POST | /api/tickets/{id}/callback | 回访工单 | operator |
| POST | /api/tickets/{id}/close | 关闭工单 | operator |
### 系统

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | / | 系统信息 |
| GET | /health | 健康检查（含数据库连通性） |
认证说明
获取Token
调用 POST /api/auth/login 获取 access_token

使用Token
后续请求在 Header 中携带：

Authorization: Bearer <token>
Token有效期
8 小时

权限级别
无：不需要登录（如登录接口、工单自动生成）
login：登录即可访问
operator：需要 admin 或 operator 角色
admin：仅 admin 角色
统一响应格式
成功响应
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin"
  }
}
错误响应
{
  "code": 404,
  "message": "账号不存在",
  "data": null
}
### 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或Token已过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 数据冲突 |
| 422 | 请求数据格式错误 |
| 500 | 服务器内部错误 |
跨模块接口说明
供 RAG 模块（成员A）调用
当 RAG 知识库无法回答用户问题时，调用以下接口自动创建工单：

POST /api/tickets/auto
Content-Type: application/json

{
  "title": "用户的问题",
  "description": "问题详细描述",
  "reporter_name": "用户姓名",
  "source": "ai_auto"
}
供前端（成员C）调用
所有接口均可通过 http://localhost:8000/docs 查看 Swagger 文档，支持在线测试。前端使用 axios 调用时需在请求头携带 JWT Token。

默认账号
用户名：admin
密码：admin123
角色：管理员
项目结构
backend/
├── app/
│   ├── main.py              # FastAPI 入口，路由注册，中间件注册
│   ├── config.py            # Pydantic Settings 配置管理
│   ├── database.py          # SQLAlchemy 连接池配置
│   ├── models/              # ORM 模型
│   │   ├── account.py       # 账号模型
│   │   └── ticket.py        # 工单+日志模型
│   ├── schemas/             # Pydantic 请求/响应格式
│   │   ├── account.py       # 账号相关 Schema
│   │   └── ticket.py        # 工单相关 Schema
│   ├── api/                 # 接口路由
│   │   ├── auth.py          # 登录接口
│   │   ├── account.py       # 账号 CRUD
│   │   └── ticket.py        # 工单全流程
│   ├── middleware/          # 中间件
│   │   ├── auth.py          # JWT 鉴权 + 权限控制
│   │   ├── exception.py     # 全局异常处理
│   │   └── logging.py       # 请求日志中间件
│   └── utils/               # 工具函数
│       ├── security.py      # 密码加密 + JWT 生成
│       └── response.py      # 统一响应格式
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量（不上传Git）
├── .env.example             # 环境变量模板
├── app.log                  # 运行日志（自动生成）
└── .gitignore
开发日志
所有 API 请求会自动记录到：

控制台输出：实时查看请求日志
app.log 文件：持久化保存，包含时间戳、请求方法、路径、状态码、耗时、IP
日志格式示例：

2026-03-28 16:01:23 [INFO] GET /api/accounts | query= | status=200 | 12.34ms | ip=127.0.0.1
2026-03-28 16:01:30 [WARNING] GET /api/accounts/9999 | query= | status=404 | 5.67ms | ip=127.0.0.1

---
