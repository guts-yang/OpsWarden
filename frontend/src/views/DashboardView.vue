<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsApi } from '@/api/analytics'
import { ticketsApi } from '@/api/tickets'
import { TICKET_STATUS, TICKET_PRIORITY, fmtDate } from '@/utils/constants'

const router = useRouter()
const stats = ref(null)
const recentTickets = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [summary, ticketData] = await Promise.all([
      analyticsApi.getSummary(),
      ticketsApi.list({ page: 1, page_size: 5 }),
    ])
    stats.value = summary
    recentTickets.value = ticketData?.items ?? []
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Stat Cards -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <div class="ops-card-hover p-5 min-h-[124px] flex flex-col">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-medium text-on-surface-variant mb-1">今日问答</p>
            <p class="text-2xl font-semibold text-on-surface tabular-nums tracking-tight">
              {{ loading ? '—' : (stats?.daily_qa ?? 0) }}
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-primary-500 text-[22px]">smart_toy</span>
          </div>
        </div>
        <p class="text-xs text-on-surface-variant mt-auto pt-3 leading-relaxed">AI 自动处理的问题数</p>
      </div>

      <div class="ops-card-hover p-5 min-h-[124px] flex flex-col">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-medium text-on-surface-variant mb-1">待处理工单</p>
            <p class="text-2xl font-semibold text-on-surface tabular-nums tracking-tight">
              {{ loading ? '—' : (stats?.pending_tickets ?? 0) }}
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-warning-container flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-warning text-[22px]">confirmation_number</span>
          </div>
        </div>
        <p class="text-xs text-on-surface-variant mt-auto pt-3 leading-relaxed">
          其中超时 {{ stats?.overdue_count ?? 0 }} 张
        </p>
      </div>

      <div class="ops-card-hover p-5 min-h-[124px] flex flex-col">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-medium text-on-surface-variant mb-1">账号总数</p>
            <p class="text-2xl font-semibold text-on-surface tabular-nums tracking-tight">
              {{ loading ? '—' : (stats?.total_accounts ?? 0) }}
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-purple-500 text-[22px]">group</span>
          </div>
        </div>
        <p class="text-xs text-on-surface-variant mt-auto pt-3 leading-relaxed">
          本月新增 {{ stats?.new_accounts_month ?? 0 }} 个
        </p>
      </div>

      <div class="ops-card-hover p-5 min-h-[124px] flex flex-col">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs font-medium text-on-surface-variant mb-1">知识库条目</p>
            <p class="text-2xl font-semibold text-on-surface tabular-nums tracking-tight">
              {{ loading ? '—' : (stats?.kb_entries ?? 0) }}
            </p>
          </div>
          <div class="w-10 h-10 rounded-xl bg-success-container flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-success text-[22px]">menu_book</span>
          </div>
        </div>
        <p class="text-xs text-on-surface-variant mt-auto pt-3 leading-relaxed">
          本周新增 {{ stats?.kb_new_week ?? 0 }} 条
        </p>
      </div>
    </div>

    <!-- Recent Tickets -->
    <div class="ops-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-outline bg-surface-dim/50">
        <div>
          <h2 class="text-sm font-semibold text-on-surface">最新工单</h2>
          <p class="text-[11px] text-on-surface-variant mt-0.5">最近 5 条，点击进入工单中心</p>
        </div>
        <button
          class="text-xs font-medium text-primary-600 hover:text-primary-700 px-2 py-1 rounded-lg hover:bg-primary-50 transition-colors"
          @click="router.push('/tickets')"
        >
          查看全部
        </button>
      </div>
      <div class="divide-y divide-outline">
        <div v-if="loading" class="px-5 py-8 text-center text-xs text-on-surface-variant">
          加载中...
        </div>
        <div
          v-else-if="recentTickets.length === 0"
          class="px-5 py-8 text-center text-xs text-on-surface-variant"
        >
          暂无工单
        </div>
        <div
          v-for="ticket in recentTickets"
          :key="ticket.id"
          class="flex items-center gap-4 px-5 py-3.5 hover:bg-primary-50/40 cursor-pointer transition-colors"
          @click="router.push('/tickets')"
        >
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <span class="text-xs text-on-surface-variant font-mono">{{ ticket.ticket_no }}</span>
              <span
                class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                :class="TICKET_PRIORITY[ticket.priority]?.class"
              >
                {{ TICKET_PRIORITY[ticket.priority]?.label }}
              </span>
            </div>
            <p class="text-sm text-on-surface truncate">{{ ticket.title }}</p>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span
              class="text-[10px] px-2 py-0.5 rounded-full font-medium"
              :class="TICKET_STATUS[ticket.status]?.class"
            >
              {{ TICKET_STATUS[ticket.status]?.label }}
            </span>
            <span class="text-xs text-on-surface-variant">{{ fmtDate(ticket.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
