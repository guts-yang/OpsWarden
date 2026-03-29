/**
 * OpsWarden 前端 API 客户端
 * 所有页面共享此模块，通过 <script src="api.js"> 引入
 */

const API_BASE = 'http://localhost:8000';

// ─── Token / 用户信息 ──────────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem('ow_token');
}

function getUser() {
  try { return JSON.parse(localStorage.getItem('ow_user') || 'null'); } catch { return null; }
}

function logout() {
  localStorage.removeItem('ow_token');
  localStorage.removeItem('ow_user');
  window.location.href = 'login.html';
}

/** 检查是否已登录，未登录则跳转 login。返回 user 对象或 null。 */
function requireAuth() {
  if (!getToken()) { window.location.href = 'login.html'; return null; }
  return getUser();
}

// ─── 基础请求封装 ──────────────────────────────────────────────────────────────

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (e) {
    throw new Error('无法连接到后端服务，请确认后端已启动（localhost:8000）');
  }

  if (res.status === 401) { logout(); throw new Error('登录已过期，请重新登录'); }

  const data = await res.json();
  if (!res.ok) {
    const msg = data.message || (Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail) || '请求失败';
    throw new Error(msg);
  }
  return data;
}

// ─── 认证接口 ──────────────────────────────────────────────────────────────────

async function login(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

// ─── 账号接口 ──────────────────────────────────────────────────────────────────

function buildQuery(params) {
  const q = new URLSearchParams(params).toString();
  return q ? '?' + q : '';
}

async function getAccounts(params = {}) {
  return request(`/api/accounts${buildQuery(params)}`);
}

async function createAccount(data) {
  return request('/api/accounts', { method: 'POST', body: JSON.stringify(data) });
}

async function updateAccount(id, data) {
  return request(`/api/accounts/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

async function freezeAccount(id) {
  return request(`/api/accounts/${id}/freeze`, { method: 'PATCH' });
}

async function unfreezeAccount(id) {
  return request(`/api/accounts/${id}/unfreeze`, { method: 'PATCH' });
}

async function resetPassword(id, newPassword) {
  return request(`/api/accounts/${id}/reset-password`, {
    method: 'PATCH',
    body: JSON.stringify({ new_password: newPassword }),
  });
}

// ─── 工单接口 ──────────────────────────────────────────────────────────────────

async function getTickets(params = {}) {
  return request(`/api/tickets${buildQuery(params)}`);
}

async function getTicket(id) {
  return request(`/api/tickets/${id}`);
}

async function getTicketLogs(id) {
  return request(`/api/tickets/${id}/logs`);
}

async function updateTicket(id, data) {
  return request(`/api/tickets/${id}`, { method: 'PUT', body: JSON.stringify(data) });
}

async function resolveTicket(id, solution, writeBack = true) {
  return request(`/api/tickets/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ solution, write_back: writeBack }),
  });
}

async function closeTicket(id) {
  return request(`/api/tickets/${id}/close`, { method: 'POST' });
}

async function createAutoTicket(title, description = '', reporterName = '') {
  return request('/api/tickets/auto', {
    method: 'POST',
    body: JSON.stringify({ title, description, reporter_name: reporterName }),
  });
}

async function createManualTicket(title, description = '', priority = 'medium') {
  return request('/api/tickets/manual', {
    method: 'POST',
    body: JSON.stringify({ title, description, priority }),
  });
}

// ─── 个人资料接口 ──────────────────────────────────────────────────────────────

async function getMe() {
  return request('/api/accounts/me');
}

async function updateMe(data) {
  return request('/api/accounts/me', { method: 'PUT', body: JSON.stringify(data) });
}

async function changePassword(oldPassword, newPassword) {
  return request('/api/accounts/me/password', {
    method: 'PATCH',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  });
}

// ─── 数据分析接口 ──────────────────────────────────────────────────────────────

async function getAnalyticsSummary() {
  return request('/api/analytics/summary');
}

async function getAnalyticsOperators() {
  return request('/api/analytics/operators');
}

// ─── 工具函数 ──────────────────────────────────────────────────────────────────

/** 格式化日期时间为 MM-DD HH:mm */
function fmtDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mi = String(d.getMinutes()).padStart(2, '0');
  return `${mm}-${dd} ${hh}:${mi}`;
}

/** 工单状态显示映射 */
const TICKET_STATUS = {
  pending:    { label: '待处理', cls: 'bg-amber-50 text-amber-600 border border-amber-100' },
  processing: { label: '处理中', cls: 'bg-blue-50 text-blue-600 border border-blue-100' },
  resolved:   { label: '已解决', cls: 'bg-emerald-50 text-secondary border border-emerald-100' },
  closed:     { label: '已关闭', cls: 'bg-slate-50 text-slate-500 border border-slate-100' },
};

/** 工单优先级显示映射 */
const TICKET_PRIORITY = {
  urgent: { label: '紧急', cls: 'text-error' },
  high:   { label: '高',   cls: 'text-amber-600' },
  medium: { label: '中',   cls: 'text-on-surface-variant' },
  low:    { label: '低',   cls: 'text-on-surface-variant' },
};

/** 账号角色显示映射 */
const ACCOUNT_ROLE = {
  admin:    { label: '管理员', cls: 'bg-red-50 text-red-600' },
  operator: { label: '运维员', cls: 'bg-blue-50 text-blue-600' },
  user:     { label: '普通用户', cls: 'bg-slate-50 text-slate-600' },
};

/** 账号状态显示映射 */
const ACCOUNT_STATUS = {
  active: { label: '正常', cls: 'bg-secondary-container/30 text-secondary', dotCls: 'bg-secondary' },
  frozen: { label: '冻结', cls: 'bg-amber-100 text-amber-700', dotCls: 'bg-amber-500' },
};

/**
 * 绑定侧边栏导航链接和退出逻辑（单次 DOM 遍历）。
 * 用 includes() 匹配文本，兼容 Material Symbols 图标的 ligature 文本。
 */
function bindSidebar() {
  const navMap = [
    ['Dashboard',      'dashboard.html'],
    ['Overview',       'dashboard.html'],
    ['Infrastructure', 'dashboard.html'],
    ['Settings',       'accounts.html'],
    ['Logs',           'tickets.html'],
    ['Incidents',      'tickets.html'],
    ['System Health',  'ai_chat.html'],
    ['Security',       'knowledge_base.html'],
    ['Analytics',      'analytics.html'],
    ['New Ticket',     'ticket_create.html'],
    ['New Scan',       'ticket_create.html'],
    ['New Deployment', 'ticket_create.html'],
    ['Profile',        'profile.html'],
    ['Assign',         'ticket_assign.html'],
    ['Network',        'network.html'],
    ['Nodes',          'nodes.html'],
    ['Automation',     'automation.html'],
    ['Documentation',  'documentation.html'],
    ['Support',        'support.html'],
    ['Applications',   'applications.html'],
    ['Cloud',          'cloud.html'],
  ];
  document.querySelectorAll('aside a, aside button, aside div[class*="cursor-pointer"], header a').forEach(el => {
    const text = el.textContent;
    if (text.includes('Logout')) {
      el.style.cursor = 'pointer';
      el.addEventListener('click', (e) => { e.preventDefault(); logout(); });
      return;
    }
    for (const [label, href] of navMap) {
      if (text.includes(label)) {
        if (el.tagName === 'BUTTON') {
          el.addEventListener('click', () => { window.location.href = href; });
        } else {
          el.href = href;
        }
        break;
      }
    }
  });
}
