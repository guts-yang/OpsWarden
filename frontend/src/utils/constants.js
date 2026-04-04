export const TICKET_STATUS = {
  pending: { label: '待处理', class: 'bg-warning-container text-warning' },
  processing: { label: '处理中', class: 'bg-primary-50 text-primary-600' },
  resolved: { label: '已解决', class: 'bg-success-container text-success' },
  closed: { label: '已关闭', class: 'bg-surface-variant text-on-surface-variant' },
}

export const TICKET_PRIORITY = {
  urgent: { label: '紧急', class: 'text-red-600 bg-red-50' },
  high: { label: '高', class: 'text-orange-600 bg-orange-50' },
  medium: { label: '中', class: 'text-yellow-600 bg-yellow-50' },
  low: { label: '低', class: 'text-green-600 bg-green-50' },
}

export const ACCOUNT_ROLE = {
  admin: { label: '管理员', class: 'bg-primary-50 text-primary-700' },
  operator: { label: '运维', class: 'bg-purple-50 text-purple-700' },
  user: { label: '普通用户', class: 'bg-surface-variant text-on-surface-variant' },
}

export const ACCOUNT_STATUS = {
  active: { label: '正常', class: 'bg-success-container text-success' },
  frozen: { label: '已冻结', class: 'bg-error-container text-error' },
}

export function fmtDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}
