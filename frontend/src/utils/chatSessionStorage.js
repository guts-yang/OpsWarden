/**
 * AI 问答会话：按登录用户 ID 分键存 sessionStorage，换账号不串历史。
 * 同标签页内跨路由保留，关标签后清空。
 */

/** 旧版全局键，仅用于启动时清理，不再写入 */
const LEGACY_THREAD_KEY = 'ow_chat_thread'
const LEGACY_MESSAGES_KEY = 'ow_chat_messages'

export function storageKeys(userId) {
  const id = String(userId)
  return {
    thread: `ow_chat_thread_${id}`,
    messages: `ow_chat_messages_${id}`,
  }
}

/** 登出时删除该用户在 sessionStorage 中的对话数据 */
export function clearChatSessionStorage(userId) {
  if (userId == null || userId === '') return
  const { thread, messages } = storageKeys(userId)
  try {
    sessionStorage.removeItem(thread)
    sessionStorage.removeItem(messages)
  } catch {
    /* ignore */
  }
}

function stripLegacyGlobalKeys() {
  try {
    sessionStorage.removeItem(LEGACY_THREAD_KEY)
    sessionStorage.removeItem(LEGACY_MESSAGES_KEY)
    localStorage.removeItem(LEGACY_THREAD_KEY)
  } catch {
    /* ignore */
  }
}

function newThreadId() {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `fallback-${Date.now()}`
}

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

function readThreadFromSession(userId) {
  try {
    const t = sessionStorage.getItem(storageKeys(userId).thread)
    return t && typeof t === 'string' && t.trim() ? t.trim() : null
  } catch {
    return null
  }
}

function readMessagesFromSession(userId) {
  try {
    const raw = sessionStorage.getItem(storageKeys(userId).messages)
    if (!raw) return null
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr) || arr.length === 0) return null
    return arr.map(parseMessage).filter(Boolean)
  } catch {
    return null
  }
}

function createAndStoreThreadId(userId) {
  const id = newThreadId()
  if (userId == null || userId === '') return id
  try {
    sessionStorage.setItem(storageKeys(userId).thread, id)
  } catch {
    /* ignore */
  }
  return id
}

/**
 * @param {number|string|undefined|null} userId 当前登录用户 id
 */
export function loadChatSession(userId) {
  stripLegacyGlobalKeys()

  if (userId == null || userId === '') {
    return {
      threadId: newThreadId(),
      messages: defaultGreetingMessages(),
    }
  }

  let threadId = readThreadFromSession(userId)
  let messages = readMessagesFromSession(userId)

  if (!threadId) {
    threadId = createAndStoreThreadId(userId)
  }

  if (!messages || messages.length === 0) {
    messages = defaultGreetingMessages()
    saveChatSession(userId, threadId, messages)
  }

  return { threadId, messages }
}

export function saveChatSession(userId, threadId, messages) {
  if (userId == null || userId === '') return
  const { thread, messages: msgKey } = storageKeys(userId)
  try {
    sessionStorage.setItem(thread, threadId)
    sessionStorage.setItem(
      msgKey,
      JSON.stringify(messages.map(serializeMessage)),
    )
  } catch {
    /* private mode / quota */
  }
}

/** 新会话：新 thread、仅欢迎语 */
export function resetChatSession(userId) {
  if (userId == null || userId === '') {
    return {
      threadId: newThreadId(),
      messages: defaultGreetingMessages(),
    }
  }
  const threadId = createAndStoreThreadId(userId)
  const messages = defaultGreetingMessages()
  saveChatSession(userId, threadId, messages)
  return { threadId, messages }
}
