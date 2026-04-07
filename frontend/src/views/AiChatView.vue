<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatApi } from '@/api/chat'
import { knowledgeApi } from '@/api/knowledge'
import { loadChatSession, saveChatSession, resetChatSession } from '@/utils/chatSessionStorage'

const initialSession = loadChatSession()
const messages = ref(initialSession.messages)
const input = ref('')
const loading = ref(false)
const chatBody = ref(null)

const threadId = ref(initialSession.threadId)

function persistSession() {
  saveChatSession(threadId.value, messages.value)
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

const MAX_LEN = 500

function pickQuickQuestionsFromKb(items, max) {
  const seen = new Set()
  const out = []
  for (const row of items || []) {
    const t = (row?.question ?? '').trim()
    if (!t || seen.has(t)) continue
    seen.add(t)
    out.push(t)
    if (out.length >= max) break
  }
  return out
}

onMounted(async () => {
  await scrollToBottom()
  try {
    const data = await knowledgeApi.list({ page: 1, page_size: 24 })
    const picked = pickQuickQuestionsFromKb(data?.items, QUICK_FROM_KB_MAX)
    quickQuestions.value = picked.length ? picked : [...FALLBACK_QUICK_QUESTIONS]
  } catch {
    quickQuestions.value = [...FALLBACK_QUICK_QUESTIONS]
  }
})

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')
}

async function scrollToBottom() {
  await nextTick()
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

async function sendMessage(text) {
  const q = (text ?? input.value).trim()
  if (!q || loading.value) return
  input.value = ''

  messages.value.push({ id: Date.now(), role: 'user', text: q, time: new Date() })
  persistSession()
  await scrollToBottom()

  loading.value = true
  try {
    const data = await chatApi.send({ query: q, thread_id: threadId.value })
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      text: data.answer,
      source: data.source,
      ticketNo: data.ticket_no,
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
    await scrollToBottom()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function clearHistory() {
  const next = resetChatSession()
  threadId.value = next.threadId
  messages.value = next.messages
}

function fmtTime(d) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-6 py-3 bg-white/95 backdrop-blur-sm border-b border-outline shadow-shell z-[1]">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary-500 text-[20px]">smart_toy</span>
        <span class="text-sm font-medium text-on-surface">AI 智能问答</span>
        <span class="text-xs bg-success-container text-success px-2 py-0.5 rounded-full">在线</span>
      </div>
      <button
        class="text-xs text-on-surface-variant hover:text-error flex items-center gap-1"
        @click="clearHistory"
      >
        <span class="material-symbols-outlined text-[14px]">delete_sweep</span>
        清空记录
      </button>
    </div>

    <!-- Messages -->
    <div ref="chatBody" class="flex-1 overflow-y-auto px-6 py-4 space-y-5 bg-gradient-to-b from-surface-dim/80 to-surface-dim">
      <div v-for="msg in messages" :key="msg.id" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        <!-- AI Avatar -->
        <div v-if="msg.role === 'ai'" class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0 mr-2 mt-0.5">
          <span class="material-symbols-outlined text-primary-500 text-[16px]">smart_toy</span>
        </div>

        <div :class="msg.role === 'user' ? 'max-w-[70%]' : 'max-w-[75%]'">
          <!-- Bubble -->
          <div
            class="px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm"
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
          <!-- Meta -->
          <div
            class="flex items-center gap-2 mt-1"
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
              v-else-if="msg.source === 'fallback'"
              class="text-[10px] bg-warning-container text-warning px-1.5 py-0.5 rounded-full font-medium"
            >
              工单已创建
              <template v-if="msg.ticketNo"> · {{ msg.ticketNo }}</template>
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
        <div v-if="msg.role === 'user'" class="w-8 h-8 rounded-full bg-primary-200 flex items-center justify-center flex-shrink-0 ml-2 mt-0.5">
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
    </div>

    <!-- Quick suggestions（文案来自知识库 question，过长时截断，title 显示全文） -->
    <div class="px-6 pb-2 flex gap-2 flex-wrap">
      <button
        v-for="(q, idx) in quickQuestions"
        :key="`${idx}-${q.slice(0, 24)}`"
        type="button"
        :title="q"
        class="text-xs px-3 py-1 rounded-full border border-outline text-on-surface-variant hover:bg-surface-container transition-colors max-w-[min(100%,14rem)] truncate text-left"
        @click="sendMessage(q)"
      >
        {{ q }}
      </button>
    </div>

    <!-- Input bar -->
    <div class="px-6 pb-6 pt-1 bg-surface-dim">
      <div
        class="bg-white border border-outline rounded-2xl p-3 flex items-end gap-3 shadow-sm focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20 transition-shadow"
      >
        <textarea
          v-model="input"
          rows="2"
          :maxlength="MAX_LEN"
          placeholder="描述您的问题... (Enter 发送，Shift+Enter 换行)"
          class="flex-1 resize-none text-sm text-on-surface bg-transparent focus:outline-none leading-relaxed"
          @keydown="onKeydown"
        />
        <div class="flex items-center gap-2 flex-shrink-0">
          <span class="text-[10px] text-on-surface-variant">{{ input.length }}/{{ MAX_LEN }}</span>
          <button
            class="w-8 h-8 rounded-xl bg-primary-500 hover:bg-primary-600 disabled:opacity-50 flex items-center justify-center transition-colors"
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
