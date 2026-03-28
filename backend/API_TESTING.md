# OpsWarden API 测试指南

## 测试环境
- 后端地址：http://localhost:8000
- Swagger UI：http://localhost:8000/docs
- 默认账号：`admin` / `admin123`

---

## 测试步骤

### 1. 登录获取 Token
在 Swagger UI 中找到 `POST /api/auth/login`，点击 **Try it out**，输入请求体：
```json
{
  "username": "admin",
  "password": "admin123"
}
```
点击 **Execute**，复制返回的 `access_token`。

---

### 2. 在 Swagger 中设置 Token
点击页面右上角 **Authorize 🔓** 按钮，在弹窗中粘贴刚才获取的 token，点击 **Authorize**，关闭弹窗即可完成全局鉴权配置。

---

### 3. 账号管理测试

#### 3.1 创建账号
```
POST /api/accounts
Content-Type: application/json
```
请求体：
```json
{
  "employee_id": "EMP001",
  "username": "zhangsan",
  "password": "123456",
  "name": "张三",
  "department": "运维部",
  "email": "zhangsan@test.com",
  "phone": "13800138000",
  "role": "operator"
}
```
**期望返回**：`code=200`，`data` 包含新账号完整信息

#### 3.2 查询账号列表
```
GET /api/accounts?page=1&page_size=20
```
**期望返回**：列表中包含刚创建的账号

#### 3.3 查询单个账号
```
GET /api/accounts/2
```
**期望返回**：返回 `id=2` 的账号完整详情

#### 3.4 冻结账号
```
PATCH /api/accounts/2/freeze
```
**期望返回**：`message="账号已冻结"`

#### 3.5 解冻账号
```
PATCH /api/accounts/2/unfreeze
```
**期望返回**：`message="账号已解冻"`

#### 3.6 重置密码
```
PATCH /api/accounts/2/reset-password
Content-Type: application/json
```
请求体：
```json
{
  "new_password": "newpass123"
}
```
**期望返回**：`message="密码已重置"`

---

### 4. 工单管理测试

#### 4.1 AI自动生成工单
```
POST /api/tickets/auto
Content-Type: application/json
```
请求体：
```json
{
  "title": "VPN无法连接公司内网",
  "description": "用户反馈VPN客户端连接后无法访问内网资源",
  "reporter_name": "李四",
  "source": "ai_auto"
}
```
**期望返回**：返回工单编号（如 `T-20260328-001`）

#### 4.2 查询工单列表
```
GET /api/tickets?page=1&page_size=20
```
**期望返回**：列表中包含刚创建的工单

#### 4.3 查询工单详情
```
GET /api/tickets/1
```
**期望返回**：返回 `id=1` 的工单完整详情

#### 4.4 更新工单
```
PUT /api/tickets/1
Content-Type: application/json
```
请求体：
```json
{
  "assignee_id": 1,
  "status": "processing",
  "priority": "high"
}
```
**期望返回**：`message="工单已更新"`

#### 4.5 解决工单
```
POST /api/tickets/1/resolve
Content-Type: application/json
```
请求体：
```json
{
  "solution": "重新安装VPN客户端并更新配置文件",
  "write_back": true
}
```
**期望返回**：`message="工单已解决"`

#### 4.6 回访工单
```
POST /api/tickets/1/callback
Content-Type: application/json
```
请求体：
```json
{
  "callback_note": "已电话回访用户，确认VPN正常使用"
}
```
**期望返回**：`message="回访记录已添加"`

#### 4.7 关闭工单
```
POST /api/tickets/1/close
```
**期望返回**：`message="工单已关闭"`

#### 4.8 查看操作日志
```
GET /api/tickets/1/logs
```
**期望返回**：包含该工单完整的操作历史记录

---

### 5. 异常处理验证

#### 5.1 查询不存在的账号
```
GET /api/accounts/9999
```
**期望返回**：
```json
{
  "code": 404,
  "message": "账号不存在",
  "data": null
}
```

#### 5.2 不带Token访问需要登录的接口
移除 `Authorization` header 后访问：
```
GET /api/accounts
```
**期望返回**：`code=403`，`message="权限不足"`

#### 5.3 参数格式错误
```
POST /api/accounts
Content-Type: application/json
```
请求体（缺失必填字段）：
```json
{
  "username": "test"
}
```
**期望返回**：`code=422`，响应包含具体缺失字段的校验信息

---

## 测试通过标准
| 测试项 | 验收状态 |
|--------|----------|
| 登录返回有效 token | ✅ |
| 创建账号成功 | ✅ |
| 查询账号列表正常 | ✅ |
| 查询账号详情正常 | ✅ |
| 冻结账号功能正常 | ✅ |
| 解冻账号功能正常 | ✅ |
| 重置密码功能正常 | ✅ |
| AI自动创建工单成功 | ✅ |
| 查询工单列表正常 | ✅ |
| 查询工单详情正常 | ✅ |
| 更新工单功能正常 | ✅ |
| 解决工单功能正常 | ✅ |
| 回访工单功能正常 | ✅ |
| 关闭工单功能正常 | ✅ |
| 查看工单日志正常 | ✅ |
| 404 异常返回统一格式 | ✅ |
| 终端输出中间件请求日志 | ✅ |
| app.log 日志文件正常生成 | ✅ |

---

## 常见问题
| 问题现象 | 解决方案 |
|----------|----------|
| Token 过期怎么办？ | 重新调用 `POST /api/auth/login` 获取新 token，重新在 Swagger 中配置即可。 |
| 接口返回 403 权限不足？ | 1. 确认已在 Swagger 右上角 Authorize 中正确设置 token；2. 确认使用的是 admin 权限账号；3. 检查 token 是否过期。 |
| 工单操作报 404 不存在？ | 1. 确认请求的工单 id 正确；2. 确认工单状态符合操作要求（如已关闭的工单无法重复执行解决操作）。 |
| 看不到中间件日志？ | 1. 确认 uvicorn 启动命令正确：`uvicorn app.main:app --reload --port 8000`；2. 检查终端实时输出；3. 查看 `backend/app.log` 日志文件是否生成。 |
