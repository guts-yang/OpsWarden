/**
 * AI 问答会话：同标签页内跨路由保留，关闭标签后 sessionStorage 清空。
 * threadId 与后端 checkpoint 对齐；消息含 ISO 时间序列化。
 */

export const CHAT_THREAD_KEY = 'ow_chat_thread'
export const CHAT_MESSAGES_KEY = 'ow_chat_messages'

function defaultGreetingMessages() {
  return [
    {
      id: 0,
      role: 'ai',
      text: '您好！我是 OpsWarden AI 助手。请描述您遇到的运维问题，我会尽力为您解答。',
      source: null,
      time: new Date(),
    },
  ]
}

function serializeMessage(m) {
  return {
    id: m.id,
    role: m.role,
    text: m.text,
    source: m.source ?? null,
    ticketNo: m.ticketNo,
    ticketId: m.ticketId,
    time: m.time instanceof Date ? m.time.toISOString() : m.time,
  }
}

function parseMessage(raw) {
  if (!raw || typeof raw !== 'object') return null
  const t = raw.time ? new Date(raw.time) : new Date()
  return {
    id: raw.id,
    role: raw.role,
    text: String(raw.text ?? ''),
    source: raw.source ?? null,
    ticketNo: raw.ticketNo,
    ticketId: raw.ticketId,
    time: Number.isNaN(t.getTime()) ? new Date() : t,
  }
}

function readThreadFromSession() {
  try {
    const t = sessionStorage.getItem(CHAT_THREAD_KEY)
    return t && typeof t === 'string' && t.trim() ? t.trim() : null
  } catch {
    return null
  }
}

function readMessagesFromSession() {
  try {
    const raw = sessionStorage.getItem(CHAT_MESSAGES_KEY)
    if (!raw) return null
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr) || arr.length === 0) return null
    return arr.map(parseMessage).filter(Boolean)
  } catch {
    return null
  }
}

/** 将旧版 localStorage 中的 thread 迁入 sessionStorage（仅当 session 尚无 thread）。 */
function migrateLegacyLocalThread() {
  try {
    const legacy = localStorage.getItem(CHAT_THREAD_KEY)
    if (!legacy || typeof legacy !== 'string' || !legacy.trim()) return null
    sessionStorage.setItem(CHAT_THREAD_KEY, legacy.trim())
    localStorage.removeItem(CHAT_THREAD_KEY)
    return legacy.trim()
  } catch {
    return null
  }
}

function createAndStoreThreadId() {
  const id =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `fallback-${Date.now()}`
  try {
    sessionStorage.setItem(CHAT_THREAD_KEY, id)
  } catch {
    /* ignore */
  }
  return id
}

/**
 * 挂载时调用：恢复 threadId + messages；必要时迁移 localStorage、写入默认欢迎语。
 */
export function loadChatSession() {
  let threadId = readThreadFromSession()
  let messages = readMessagesFromSession()

  if (!threadId) {
    threadId = migrateLegacyLocalThread() || createAndStoreThreadId()
  }

  if (!messages || messages.length === 0) {
    messages = defaultGreetingMessages()
    saveChatSession(threadId, messages)
  }

  return { threadId, messages }
}

export function saveChatSession(threadId, messages) {
  try {
    sessionStorage.setItem(CHAT_THREAD_KEY, threadId)
    sessionStorage.setItem(
      CHAT_MESSAGES_KEY,
      JSON.stringify(messages.map(serializeMessage)),
    )
  } catch {
    /* private mode / quota */
  }
}

/** 新会话：新 thread、仅欢迎语，并写入 sessionStorage。 */
export function resetChatSession() {
  const threadId = createAndStoreThreadId()
  const messages = defaultGreetingMessages()
  saveChatSession(threadId, messages)
  try {
    localStorage.removeItem(CHAT_THREAD_KEY)
  } catch {
    /* ignore */
  }
  return { threadId, messages }
}
