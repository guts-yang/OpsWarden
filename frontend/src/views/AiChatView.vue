<script setup>
import { ref, nextTick, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { chatApi } from '@/api/chat'
import { knowledgeApi } from '@/api/knowledge'
import { useAuthStore } from '@/stores/auth'
import { loadChatSession, saveChatSession, resetChatSession } from '@/utils/chatSessionStorage'

const auth = useAuthStore()
const route = useRoute()

const initialSession = loadChatSession(auth.user?.id)
const messages = ref(initialSession.messages)
const input = ref('')
const loading = ref(false)
const chatBody = ref(null)

const threadId = ref(initialSession.threadId)
const messagesEndRef = ref(null)

function persistSession() {
  saveChatSession(auth.user?.id, threadId.value, messages.value)
}

/** 与知识库列表接口顺序一致：updated_at 降序，取前若干条 question */
const QUICK_FROM_KB_MAX = 8
const FALLBACK_QUICK_QUESTIONS = [
  '账号无法登录怎么办？',
  'VPN 连接失败如何处理？',
  '服务器磁盘空间不足',
  '数据库连接超时',
]

const quickQuestions = ref([...FALLBACK_QUICK_QUESTIONS])

/** 手机端只显示前 3 条快捷问题，PC 端全部显示 */
const isMobile = ref(false)
function updateIsMobile() {
  isMobile.value =
    typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches
}
const visibleQuickQuestions = computed(() =>
  isMobile.value ? quickQuestions.value.slice(0, 3) : quickQuestions.value,
)

const MAX_LEN = 500

/** 解析 quick-prompts 响应（兼容拦截器已解包或仍带 data 信封） */
function normalizeQuickQuestionsPayload(raw) {
  if (!raw || typeof raw !== 'object') return null
  let qs = raw.questions
  if (!Array.isArray(qs) && raw.data != null && typeof raw.data === 'object') {
    qs = raw.data.questions
  }
  if (!Array.isArray(qs) || qs.length === 0) return null
  const out = qs.map((s) => String(s).trim()).filter(Boolean)
  return out.length ? out : null
}

async function refreshQuickQuestionsFromKb() {
  try {
    const raw = await knowledgeApi.quickPrompts({ limit: QUICK_FROM_KB_MAX })
    const list = normalizeQuickQuestionsPayload(raw)
    if (list) {
      quickQuestions.value = list
      return
    }
  } catch {
    /* 网络/401 等：回落模板 */
  }
  quickQuestions.value = [...FALLBACK_QUICK_QUESTIONS]
}

watch(
  () => route.name,
  (name) => {
    if (name === 'AiChat') refreshQuickQuestionsFromKb()
  },
  { immediate: true },
)

watch(
  () => auth.user?.id,
  () => {
    if (route.name === 'AiChat') refreshQuickQuestionsFromKb()
  },
)

onMounted(async () => {
  updateIsMobile()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', updateIsMobile)
  }
  await scrollToBottom()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateIsMobile)
  }
})

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')
}

async function scrollToBottom() {
  await nextTick()
  // 优先用锚点元素 scrollIntoView，确保不论哪层是滚动容器都能滚到底
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: 'smooth', block: 'end' })
    return
  }
  // 回退：直接操作滚动容器
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

async function sendMessage(text, pendingAction = null) {
  const q = (text ?? input.value).trim()
  if (!q || loading.value) return
  input.value = ''

  messages.value.push({ id: Date.now(), role: 'user', text: q, time: new Date() })
  persistSession()
  await scrollToBottom()

  loading.value = true
  try {
    const data = await chatApi.send({
      query: q,
      thread_id: threadId.value,
      pending_action: pendingAction,
    })
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      text: data.answer,
      source: data.source,
      ticketNo: data.ticket_no,
      needsConfirmation: data.needs_confirmation,
      pendingAction: data.pending_action,
      time: new Date(),
    })
  } catch (e) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      text: `请求失败：${e.message}`,
      source: 'error',
      time: new Date(),
    })
  } finally {
    persistSession()
    loading.value = false
    // 等待 loading 气泡消失、AI 消息气泡渲染完成后再滚动
    await nextTick()
    await scrollToBottom()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function confirmPending(msg) {
  if (loading.value) return
  msg.needsConfirmation = false
  persistSession()
  sendMessage('确认创建工单', msg.pendingAction)
}

function cancelPending(msg) {
  if (loading.value) return
  msg.needsConfirmation = false
  persistSession()
  sendMessage('暂不创建工单', msg.pendingAction)
}

function clearHistory() {
  const next = resetChatSession(auth.user?.id)
  threadId.value = next.threadId
  messages.value = next.messages
}

function fmtTime(d) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="flex flex-col flex-1 min-h-0">
    <!-- Toolbar -->
    <div class="flex-shrink-0 flex items-center justify-between px-3 md:px-6 py-2.5 md:py-3 bg-white/95 backdrop-blur-sm border-b border-outline shadow-shell z-[1]">
      <div class="flex items-center gap-2 min-w-0">
        <span class="material-symbols-outlined text-primary-500 text-[20px] shrink-0">smart_toy</span>
        <span class="text-sm font-medium text-on-surface truncate">AI 智能问答</span>
        <span class="text-xs bg-success-container text-success px-2 py-0.5 rounded-full shrink-0">在线</span>
      </div>
      <button
        type="button"
        class="text-xs text-on-surface-variant hover:text-error active:text-error flex items-center gap-1 px-2 py-1 rounded-md hover:bg-surface-container shrink-0"
        @click="clearHistory"
      >
        <span class="material-symbols-outlined text-[14px]">delete_sweep</span>
        <span class="hidden sm:inline">清空记录</span>
      </button>
    </div>

    <!-- Messages -->
    <div
      ref="chatBody"
      class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-3 md:px-6 py-3 md:py-4 space-y-4 md:space-y-5 bg-gradient-to-b from-surface-dim/80 to-surface-dim"
    >
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- AI Avatar -->
        <div
          v-if="msg.role === 'ai'"
          class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mr-2 mt-0.5"
        >
          <span class="material-symbols-outlined text-primary-500 text-[16px]">smart_toy</span>
        </div>

        <div
          class="min-w-0"
          :class="msg.role === 'user' ? 'max-w-[82%] md:max-w-[70%]' : 'max-w-[82%] md:max-w-[75%]'"
        >
          <!-- Bubble -->
          <div
            class="px-3.5 md:px-4 py-2.5 md:py-3 rounded-2xl text-sm leading-relaxed shadow-sm break-words whitespace-pre-wrap"
            :class="
              msg.role === 'user'
                ? 'bg-primary-500 text-white rounded-tr-md shadow-lift'
                : msg.source === 'error'
                  ? 'bg-error-container border border-error/20 text-on-surface rounded-tl-md'
                  : msg.id === 0
                    ? 'bg-white border border-outline text-on-surface rounded-tl-md ring-1 ring-primary-500/10'
                    : 'bg-white border border-outline text-on-surface rounded-tl-md'
            "
            v-html="escapeHtml(msg.text)"
          />
          <div
            v-if="msg.role === 'ai' && msg.needsConfirmation && msg.pendingAction?.tool === 'ticket_create'"
            class="mt-2 flex flex-wrap gap-2"
          >
            <button
              type="button"
              class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary-500 text-white text-xs font-medium hover:bg-primary-600 active:bg-primary-700 disabled:opacity-50"
              :disabled="loading"
              @click="confirmPending(msg)"
            >
              <span class="material-symbols-outlined text-[14px]">confirmation_number</span>
              创建工单
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-outline bg-white text-on-surface-variant text-xs font-medium hover:bg-surface-container disabled:opacity-50"
              :disabled="loading"
              @click="cancelPending(msg)"
            >
              <span class="material-symbols-outlined text-[14px]">close</span>
              暂不创建
            </button>
          </div>
          <!-- Meta -->
          <div
            class="flex items-center gap-2 mt-1 flex-wrap"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <span class="text-[10px] text-on-surface-variant">{{ fmtTime(msg.time) }}</span>
            <span
              v-if="msg.source === 'kb'"
              class="text-[10px] bg-success-container text-success px-1.5 py-0.5 rounded-full"
            >
              知识库命中
            </span>
            <span
              v-else-if="msg.ticketNo"
              class="text-[10px] bg-warning-container text-warning px-1.5 py-0.5 rounded-full font-medium"
            >
              工单已创建
              <template v-if="msg.ticketNo"> · {{ msg.ticketNo }}</template>
            </span>
            <span
              v-else-if="msg.needsConfirmation"
              class="text-[10px] bg-warning-container text-warning px-1.5 py-0.5 rounded-full font-medium"
            >
              等待确认
            </span>
            <span
              v-else-if="msg.source === 'error'"
              class="text-[10px] bg-error-container text-error px-1.5 py-0.5 rounded-full font-medium"
            >
              请求失败
            </span>
          </div>
        </div>

        <!-- User Avatar -->
        <div
          v-if="msg.role === 'user'"
          class="w-8 h-8 rounded-full bg-primary-200 flex items-center justify-center flex-shrink-0 ml-2 mt-0.5"
        >
          <span class="material-symbols-outlined text-primary-700 text-[16px]">person</span>
        </div>
      </div>

      <!-- Loading indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mr-2">
          <span class="material-symbols-outlined text-primary-500 text-[16px]">smart_toy</span>
        </div>
        <div class="bg-white border border-outline rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1.5 items-center">
          <span class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce" style="animation-delay:0s" />
          <span class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce" style="animation-delay:.15s" />
          <span class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce" style="animation-delay:.3s" />
        </div>
      </div>

      <!-- 滚动锚点：发消息后 scrollIntoView 到此处 -->
      <div ref="messagesEndRef" class="h-px" />
    </div>

    <!-- Quick suggestions：手机端最多 3 条；PC 端全部 -->
    <div
      v-if="visibleQuickQuestions.length > 0"
      class="flex-shrink-0 border-t border-outline px-3 md:px-6 pt-2 pb-2 flex gap-2 flex-wrap bg-surface-dim"
    >
      <button
        v-for="(q, idx) in visibleQuickQuestions"
        :key="`${idx}-${q.slice(0, 24)}`"
        type="button"
        :title="q"
        class="text-xs px-3 py-1.5 rounded-full border border-outline bg-white text-on-surface-variant hover:bg-surface-container active:bg-surface-container transition-colors max-w-full truncate text-left"
        @click="sendMessage(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- Input bar：底部安全区 + TabBar 让位（手机端） -->
    <div
      class="flex-shrink-0 px-3 md:px-6 pb-3 md:pb-6 pt-2 bg-surface-dim mb-[calc(64px+env(safe-area-inset-bottom))] md:mb-0"
    >
      <div
        class="bg-white border border-outline rounded-2xl p-2.5 md:p-3 flex items-end gap-2 md:gap-3 shadow-sm focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20 transition-shadow"
      >
        <textarea
          v-model="input"
          rows="2"
          :maxlength="MAX_LEN"
          placeholder="描述您的问题..."
          class="flex-1 min-w-0 resize-none text-sm text-on-surface bg-transparent focus:outline-none leading-relaxed"
          @keydown="onKeydown"
        />
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="text-[10px] text-on-surface-variant tabular-nums">{{ input.length }}/{{ MAX_LEN }}</span>
          <button
            type="button"
            class="w-9 h-9 md:w-8 md:h-8 rounded-xl bg-primary-500 hover:bg-primary-600 active:bg-primary-700 disabled:opacity-50 flex items-center justify-center transition-colors"
            :disabled="!input.trim() || loading"
            @click="sendMessage()"
          >
            <span class="material-symbols-outlined text-white text-[18px]">send</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
