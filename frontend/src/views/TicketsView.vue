<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ticketsApi } from '@/api/tickets'
import { useAuthStore } from '@/stores/auth'
import BaseModal from '@/components/BaseModal.vue'
import BasePagination from '@/components/BasePagination.vue'
import { TICKET_STATUS, TICKET_PRIORITY, fmtDate } from '@/utils/constants'

const auth = useAuthStore()

const tabs = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待处理' },
  { key: 'processing', label: '处理中' },
  { key: 'resolved', label: '已解决' },
  { key: 'closed', label: '已关闭' },
]

const activeTab = ref('')
const keyword = ref('')
const page = ref(1)
const PAGE_SIZE = 15
const tickets = ref([])
const total = ref(0)
const loading = ref(false)

const selectedTicket = ref(null)
const ticketLogs = ref([])
const detailLoading = ref(false)

const showCreateModal = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = reactive({ title: '', description: '', priority: 'medium' })

const resolving = ref(false)
const resolveForm = reactive({ solution: '', write_back: false })

async function loadTickets() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: PAGE_SIZE }
    if (activeTab.value) params.status = activeTab.value
    if (keyword.value) params.keyword = keyword.value
    const data = await ticketsApi.list(params)
    tickets.value = data?.items ?? []
    total.value = data?.total ?? 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function selectTicket(ticket) {
  selectedTicket.value = ticket
  ticketLogs.value = []
  detailLoading.value = true
  try {
    const [detail, logs] = await Promise.all([
      ticketsApi.get(ticket.id),
      ticketsApi.getLogs(ticket.id),
    ])
    selectedTicket.value = detail
    ticketLogs.value = logs ?? []
  } catch (e) {
    console.error(e)
  } finally {
    detailLoading.value = false
  }
}

async function createTicket() {
  if (!createForm.title.trim()) {
    createError.value = '请输入工单标题'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    await ticketsApi.createManual({
      title: createForm.title.trim(),
      description: createForm.description.trim(),
      priority: createForm.priority,
    })
    showCreateModal.value = false
    Object.assign(createForm, { title: '', description: '', priority: 'medium' })
    await loadTickets()
  } catch (e) {
    createError.value = e.message
  } finally {
    creating.value = false
  }
}

async function resolveTicket() {
  if (!resolveForm.solution.trim()) return
  resolving.value = true
  try {
    const updated = await ticketsApi.resolve(selectedTicket.value.id, {
      solution: resolveForm.solution.trim(),
      write_back: resolveForm.write_back,
    })
    selectedTicket.value = updated
    resolveForm.solution = ''
    resolveForm.write_back = false
    await loadTickets()
  } catch (e) {
    alert(`解决失败：${e.message}`)
  } finally {
    resolving.value = false
  }
}

async function closeTicket() {
  if (!confirm('确认关闭该工单？')) return
  try {
    await ticketsApi.close(selectedTicket.value.id)
    await Promise.all([selectTicket(selectedTicket.value), loadTickets()])
  } catch (e) {
    alert(`操作失败：${e.message}`)
  }
}

onMounted(loadTickets)
watch(activeTab, () => { page.value = 1; loadTickets() })

let searchTimer
function onKeywordInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadTickets() }, 400)
}

function onPageChange(p) {
  page.value = p
  loadTickets()
}
</script>

<template>
  <div class="flex h-full overflow-hidden">
    <!-- Left: list -->
<<<<<<< HEAD
    <div class="w-[38%] min-w-[280px] max-w-[420px] flex-shrink-0 border-r border-outline flex flex-col bg-white shadow-shell">
=======
    <div class="w-[38%] flex-shrink-0 border-r border-outline flex flex-col bg-white">
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
      <!-- Header -->
      <div class="px-4 pt-4 pb-3 border-b border-outline space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-on-surface">工单列表</h2>
          <button
            class="flex items-center gap-1 text-xs bg-primary-500 text-white px-3 py-1.5 rounded-lg hover:bg-primary-600"
            @click="showCreateModal = true"
          >
            <span class="material-symbols-outlined text-[14px]">add</span>
            新建
          </button>
        </div>
        <!-- Search -->
        <div class="relative">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">
            search
          </span>
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索工单..."
<<<<<<< HEAD
            class="w-full pl-8 pr-3 py-2 text-xs ops-input"
=======
            class="w-full pl-8 pr-3 py-1.5 text-xs border border-outline rounded-lg focus:outline-none focus:border-primary-500"
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
            @input="onKeywordInput"
          />
        </div>
        <!-- Tabs -->
        <div class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            class="px-2.5 py-1 text-xs rounded-md transition-colors"
            :class="
              activeTab === tab.key
                ? 'bg-primary-50 text-primary-700 font-medium'
                : 'text-on-surface-variant hover:bg-surface-container'
            "
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- List -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="loading" class="text-center py-12 text-xs text-on-surface-variant">加载中...</div>
        <div v-else-if="tickets.length === 0" class="text-center py-12 text-xs text-on-surface-variant">暂无工单</div>
        <div
          v-for="ticket in tickets"
          :key="ticket.id"
          class="px-4 py-3 border-b border-outline cursor-pointer transition-colors"
          :class="selectedTicket?.id === ticket.id ? 'bg-primary-50' : 'hover:bg-surface-dim'"
          @click="selectTicket(ticket)"
        >
          <div class="flex items-center justify-between mb-1">
            <span class="text-[10px] text-on-surface-variant font-mono">{{ ticket.ticket_no }}</span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
              :class="TICKET_STATUS[ticket.status]?.class"
            >
              {{ TICKET_STATUS[ticket.status]?.label }}
            </span>
          </div>
          <p class="text-xs font-medium text-on-surface truncate mb-1">{{ ticket.title }}</p>
          <div class="flex items-center gap-2">
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full"
              :class="TICKET_PRIORITY[ticket.priority]?.class"
            >
              {{ TICKET_PRIORITY[ticket.priority]?.label }}
            </span>
            <span class="text-[10px] text-on-surface-variant ml-auto">{{ fmtDate(ticket.created_at) }}</span>
          </div>
        </div>
      </div>

      <div class="px-4 pb-3">
        <BasePagination :total="total" :page="page" :page-size="PAGE_SIZE" @update:page="onPageChange" />
      </div>
    </div>

    <!-- Right: detail -->
    <div class="flex-1 overflow-y-auto p-6 bg-surface-dim">
<<<<<<< HEAD
      <div v-if="!selectedTicket" class="flex flex-col items-center justify-center h-full text-on-surface-variant px-6">
        <div class="w-16 h-16 rounded-2xl bg-surface-container flex items-center justify-center mb-4">
          <span class="material-symbols-outlined text-4xl text-on-surface-variant/40">confirmation_number</span>
        </div>
        <p class="text-sm font-medium text-on-surface">选择工单</p>
        <p class="text-xs text-on-surface-variant mt-1 text-center max-w-[240px]">从左侧列表点选一条工单即可查看描述、处理与操作记录</p>
=======
      <div v-if="!selectedTicket" class="flex flex-col items-center justify-center h-full text-on-surface-variant">
        <span class="material-symbols-outlined text-5xl mb-3 opacity-30">confirmation_number</span>
        <p class="text-sm">从左侧选择一个工单查看详情</p>
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
      </div>

      <div v-else-if="detailLoading" class="text-center py-12 text-xs text-on-surface-variant">
        加载中...
      </div>

      <div v-else class="space-y-4">
        <!-- Title row -->
<<<<<<< HEAD
        <div class="ops-card p-5">
=======
        <div class="bg-white rounded-xl border border-outline p-5">
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
          <div class="flex items-start justify-between gap-3 mb-3">
            <h3 class="text-base font-semibold text-on-surface">{{ selectedTicket.title }}</h3>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span
                class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="TICKET_PRIORITY[selectedTicket.priority]?.class"
              >
                {{ TICKET_PRIORITY[selectedTicket.priority]?.label }}
              </span>
              <span
                class="text-xs px-2 py-0.5 rounded-full font-medium"
                :class="TICKET_STATUS[selectedTicket.status]?.class"
              >
                {{ TICKET_STATUS[selectedTicket.status]?.label }}
              </span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
            <div>
              <span class="text-on-surface-variant">工单号：</span>
              <span class="font-mono">{{ selectedTicket.ticket_no }}</span>
            </div>
            <div>
              <span class="text-on-surface-variant">来源：</span>
              <span>{{ selectedTicket.source === 'ai_auto' ? 'AI 自动' : '手动创建' }}</span>
            </div>
            <div>
              <span class="text-on-surface-variant">提交人：</span>
              <span>{{ selectedTicket.reporter_name || '—' }}</span>
            </div>
            <div>
              <span class="text-on-surface-variant">创建时间：</span>
              <span>{{ fmtDate(selectedTicket.created_at) }}</span>
            </div>
          </div>
          <div v-if="selectedTicket.description" class="mt-3 pt-3 border-t border-outline">
            <p class="text-xs text-on-surface-variant mb-1">问题描述</p>
            <p class="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">{{ selectedTicket.description }}</p>
          </div>
        </div>

        <!-- Solution (resolved) -->
<<<<<<< HEAD
        <div v-if="selectedTicket.solution" class="ops-card p-5">
=======
        <div v-if="selectedTicket.solution" class="bg-white rounded-xl border border-outline p-5">
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
          <p class="text-xs font-medium text-on-surface-variant mb-2">解决方案</p>
          <p class="text-sm text-on-surface leading-relaxed whitespace-pre-wrap">{{ selectedTicket.solution }}</p>
          <div class="flex items-center gap-3 mt-3 text-xs text-on-surface-variant">
            <span>解决于 {{ fmtDate(selectedTicket.resolved_at) }}</span>
            <span v-if="selectedTicket.is_written_back" class="text-success">已写入知识库</span>
          </div>
        </div>

        <!-- Resolve form (operator, pending/processing) -->
        <div
          v-if="auth.isOperator && ['pending', 'processing'].includes(selectedTicket.status)"
<<<<<<< HEAD
          class="ops-card p-5"
=======
          class="bg-white rounded-xl border border-outline p-5"
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
        >
          <p class="text-xs font-medium text-on-surface-variant mb-3">处理工单</p>
          <textarea
            v-model="resolveForm.solution"
            rows="4"
            placeholder="请填写解决方案..."
<<<<<<< HEAD
            class="w-full ops-input px-3 py-2 text-sm resize-none mb-3"
=======
            class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 resize-none mb-3"
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
          />
          <div class="flex items-center justify-between">
            <label class="flex items-center gap-2 text-xs text-on-surface-variant cursor-pointer">
              <input v-model="resolveForm.write_back" type="checkbox" class="rounded" />
              写入知识库
            </label>
            <button
              class="px-4 py-1.5 bg-success text-white text-xs rounded-lg hover:bg-green-700 disabled:opacity-60"
              :disabled="!resolveForm.solution.trim() || resolving"
              @click="resolveTicket"
            >
              {{ resolving ? '提交中...' : '标记已解决' }}
            </button>
          </div>
        </div>

        <!-- Close button -->
        <div
          v-if="auth.isOperator && selectedTicket.status === 'resolved'"
          class="flex justify-end"
        >
          <button
            class="px-4 py-1.5 border border-outline text-xs rounded-lg hover:bg-surface-container"
            @click="closeTicket"
          >
            关闭工单
          </button>
        </div>

        <!-- Logs -->
<<<<<<< HEAD
        <div class="ops-card p-5">
=======
        <div class="bg-white rounded-xl border border-outline p-5">
>>>>>>> 32629c1c2d2595ea4edddeb2b46ff4d551f18285
          <p class="text-xs font-medium text-on-surface-variant mb-3">操作记录</p>
          <div v-if="ticketLogs.length === 0" class="text-xs text-on-surface-variant">暂无记录</div>
          <div class="space-y-3">
            <div
              v-for="log in ticketLogs"
              :key="log.id"
              class="flex gap-3"
            >
              <div class="w-1.5 h-1.5 rounded-full bg-outline mt-1.5 flex-shrink-0" />
              <div>
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="text-xs font-medium text-on-surface">{{ log.action }}</span>
                  <span class="text-[10px] text-on-surface-variant">{{ log.operator_name }}</span>
                  <span class="text-[10px] text-on-surface-variant ml-auto">{{ fmtDate(log.created_at) }}</span>
                </div>
                <p v-if="log.content" class="text-xs text-on-surface-variant">{{ log.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Create Modal -->
  <BaseModal
    :show="showCreateModal"
    title="新建工单"
    confirm-text="提交"
    :loading="creating"
    @confirm="createTicket"
    @cancel="showCreateModal = false"
  >
    <div class="space-y-4">
      <div v-if="createError" class="text-xs text-error bg-error-container px-3 py-2 rounded-lg">
        {{ createError }}
      </div>
      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">标题 <span class="text-error">*</span></label>
        <input
          v-model="createForm.title"
          type="text"
          placeholder="请简要描述问题"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">详细描述</label>
        <textarea
          v-model="createForm.description"
          rows="4"
          placeholder="请详细描述问题现象、影响范围等..."
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 resize-none"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">优先级</label>
        <select
          v-model="createForm.priority"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        >
          <option value="low">低</option>
          <option value="medium">中</option>
          <option value="high">高</option>
          <option value="urgent">紧急</option>
        </select>
      </div>
    </div>
  </BaseModal>
</template>
