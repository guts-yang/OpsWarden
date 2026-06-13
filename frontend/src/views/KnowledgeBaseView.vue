<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { knowledgeApi } from '@/api/knowledge'
import BasePagination from '@/components/BasePagination.vue'
import BaseSlidePanel from '@/components/BaseSlidePanel.vue'
import { fmtDate } from '@/utils/constants'

const categories = ['全部', '账号与权限管理', '网络与连接问题', '服务器与系统运维', '应用与数据库', '安全与审计', '监控与告警', '办公设备与环境', '差旅报销与入职离职事务']
const sourceOptions = [
  { value: '', label: '全部来源' },
  { value: 'manual', label: '手动录入' },
  { value: 'ticket_writeback', label: '工单回写' },
]

const stats = ref(null)
const entries = ref([])
const total = ref(0)
const loading = ref(false)
const activeCategory = ref('全部')
const searchKeyword = ref('')
const sourceFilter = ref('')
const page = ref(1)
const PAGE_SIZE = 12

// 自检质量分（match_score）口径文案，全局统一
const MATCH_SCORE_TOOLTIP =
  '自检质量分：基于语义模型计算问题与解决方案的余弦相似度，反映该条知识问答对的内在一致性，与实际检索命中率无关。'

const showPanel = ref(false)
const editingEntry = ref(null)
const saving = ref(false)
const panelError = ref('')

const form = reactive({
  category: '基础架构',
  question: '',
  solution: '',
  tags: '',
})

async function loadStats() {
  try {
    stats.value = await knowledgeApi.getStats()
  } catch {}
}

async function loadEntries() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: PAGE_SIZE,
    }
    if (activeCategory.value !== '全部') params.category = activeCategory.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (sourceFilter.value) params.source = sourceFilter.value

    const data = await knowledgeApi.list(params)
    entries.value = data?.items ?? []
    total.value = data?.total ?? 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
  loadEntries()
})

watch([activeCategory, sourceFilter], () => {
  page.value = 1
  loadEntries()
})

let searchTimer
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadEntries()
  }, 400)
}

function onPageChange(p) {
  page.value = p
  loadEntries()
}

function openCreate() {
  editingEntry.value = null
  Object.assign(form, {
    category: '基础架构',
    question: '',
    solution: '',
    tags: '',
  })
  panelError.value = ''
  showPanel.value = true
}

function openEdit(entry) {
  editingEntry.value = entry
  Object.assign(form, {
    category: entry.category,
    question: entry.question,
    solution: entry.solution,
    tags: Array.isArray(entry.tags) ? entry.tags.join(', ') : (entry.tags ?? ''),
  })
  panelError.value = ''
  showPanel.value = true
}

async function saveEntry() {
  if (!form.question.trim() || !form.solution.trim()) {
    panelError.value = '问题和解决方案不能为空'
    return
  }
  saving.value = true
  panelError.value = ''
  try {
    const tagStr = form.tags
      ? form.tags.split(',').map((t) => t.trim()).filter(Boolean).join(', ')
      : ''
    const payload = {
      category: form.category,
      question: form.question.trim(),
      solution: form.solution.trim(),
      tags: tagStr || undefined,
    }
    if (editingEntry.value) {
      await knowledgeApi.update(editingEntry.value.id, payload)
    } else {
      await knowledgeApi.create(payload)
    }
    showPanel.value = false
    await Promise.all([loadStats(), loadEntries()])
  } catch (e) {
    panelError.value = e.message
  } finally {
    saving.value = false
  }
}

async function deleteEntry(entry) {
  if (!confirm(`确认删除「${entry.question}」？此操作不可恢复。`)) return
  try {
    await knowledgeApi.remove(entry.id)
    await Promise.all([loadStats(), loadEntries()])
  } catch (e) {
    alert(`删除失败：${e.message}`)
  }
}

const panelTitle = computed(() => (editingEntry.value ? '编辑知识条目' : '新增知识条目'))
</script>

<template>
  <div class="p-4 md:p-6 space-y-4 md:space-y-5 max-w-full overflow-x-hidden">
    <!-- Stats -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-3 md:gap-4">
      <div class="ops-card-hover p-3 md:p-4 min-h-[92px] md:min-h-[100px] flex flex-col">
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-on-surface-variant">总条目</p>
          <div class="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-primary-50 flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-primary-500 text-[16px] md:text-[18px]">library_books</span>
          </div>
        </div>
        <p class="text-xl md:text-2xl font-semibold text-on-surface mt-2 tabular-nums">{{ stats?.total ?? '—' }}</p>
      </div>
      <div class="ops-card-hover p-3 md:p-4 min-h-[92px] md:min-h-[100px] flex flex-col">
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-on-surface-variant">本周新增</p>
          <div class="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-success-container flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-success text-[16px] md:text-[18px]">trending_up</span>
          </div>
        </div>
        <p class="text-xl md:text-2xl font-semibold text-on-surface mt-2 tabular-nums">{{ stats?.new_this_week ?? '—' }}</p>
      </div>
      <div class="ops-card-hover p-3 md:p-4 min-h-[92px] md:min-h-[100px] flex flex-col">
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-on-surface-variant">工单回写</p>
          <div class="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-warning-container flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-warning text-[16px] md:text-[18px]">sync_alt</span>
          </div>
        </div>
        <p class="text-xl md:text-2xl font-semibold text-on-surface mt-2 tabular-nums">{{ stats?.ticket_writeback ?? '—' }}</p>
      </div>
      <div class="ops-card-hover p-3 md:p-4 min-h-[92px] md:min-h-[100px] flex flex-col">
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-on-surface-variant flex items-center gap-1 min-w-0">
            <span class="truncate">平均匹配分</span>
            <span
              class="material-symbols-outlined text-[14px] text-on-surface-variant/70 cursor-help shrink-0"
              :title="MATCH_SCORE_TOOLTIP"
            >info</span>
          </p>
          <div class="w-7 h-7 md:w-8 md:h-8 rounded-lg bg-surface-container flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-on-surface-variant text-[16px] md:text-[18px]">analytics</span>
          </div>
        </div>
        <p class="text-xl md:text-2xl font-semibold text-on-surface mt-2 tabular-nums">
          {{ stats?.avg_match_score != null ? (stats.avg_match_score * 100).toFixed(0) + '%' : '—' }}
        </p>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <!-- Category tabs：手机端横向可滚（系统组件，与条目卡片无关） -->
      <div class="flex items-center gap-2 overflow-x-auto no-scrollbar -mx-4 md:mx-0 px-4 md:px-0 pb-1 -mb-1 lg:pb-0 lg:mb-0">
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          class="px-3 py-1.5 text-xs rounded-lg border transition-colors shrink-0 whitespace-nowrap"
          :class="
            activeCategory === cat
              ? 'bg-primary-500 text-white border-primary-500 shadow-sm'
              : 'border-outline text-on-surface-variant hover:bg-surface-container'
          "
          @click="activeCategory = cat"
        >
          {{ cat }}
        </button>
      </div>

      <!-- Filter inputs：手机端堆叠 -->
      <div class="grid grid-cols-2 gap-2 lg:flex lg:items-center lg:gap-2">
        <select
          v-model="sourceFilter"
          class="text-xs ops-input px-3 py-2 cursor-pointer w-full lg:w-auto col-span-1"
        >
          <option v-for="opt in sourceOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <div class="relative col-span-1 lg:col-auto">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant">
            search
          </span>
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索关键词"
            class="w-full lg:w-48 pl-8 pr-3 py-2 text-xs ops-input"
            @input="onSearchInput"
          />
        </div>
        <button
          type="button"
          class="col-span-2 lg:col-auto flex items-center justify-center gap-1.5 px-3 py-2 bg-primary-500 text-white text-xs rounded-lg hover:bg-primary-600 active:bg-primary-700 min-h-[36px]"
          @click="openCreate"
        >
          <span class="material-symbols-outlined text-[14px]">add</span>
          新增条目
        </button>
      </div>
    </div>

    <!-- Grid：手机端单列；条目卡片严格不溢出，仅垂直滚动 -->
    <div v-if="loading" class="text-center py-16 text-xs text-on-surface-variant">加载中...</div>
    <div v-else-if="entries.length === 0" class="text-center py-16 text-xs text-on-surface-variant">暂无数据</div>
    <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-3 md:gap-4">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="ops-card-hover p-3 md:p-4 group w-full min-w-0 overflow-hidden"
      >
        <div class="flex items-start justify-between gap-2 md:gap-3">
          <div class="flex-1 min-w-0">
            <!-- 顶部徽章行：可换行不溢出 -->
            <div class="flex items-center gap-1.5 mb-2 flex-wrap">
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-primary-50 text-primary-700 font-medium max-w-full truncate">
                {{ entry.category }}
              </span>
              <span
                class="text-[10px] px-2 py-0.5 rounded-full font-medium"
                :class="
                  entry.source === 'ticket_writeback'
                    ? 'bg-warning-container text-warning'
                    : 'bg-surface-variant text-on-surface-variant'
                "
              >
                {{ entry.source === 'ticket_writeback' ? '工单回写' : '手动' }}
              </span>
              <span
                v-if="entry.match_score != null"
                class="text-[10px] text-on-surface-variant md:ml-auto inline-flex items-center gap-0.5 cursor-help"
                :title="MATCH_SCORE_TOOLTIP"
              >
                匹配 {{ (entry.match_score * 100).toFixed(0) }}%
                <span class="material-symbols-outlined text-[12px] text-on-surface-variant/70">info</span>
              </span>
            </div>
            <!-- 问题：截断不换行溢出 -->
            <p class="text-sm font-medium text-on-surface mb-1 line-clamp-2 break-words">{{ entry.question }}</p>
            <!-- 解决方案预览：换行 + 截断 -->
            <p class="text-xs text-on-surface-variant line-clamp-2 leading-relaxed break-words">{{ entry.solution }}</p>
            <p class="text-[10px] text-on-surface-variant mt-2">更新于 {{ fmtDate(entry.updated_at) }}</p>
          </div>
          <!-- Actions：手机端常显，PC 端 hover 显示 -->
          <div class="flex flex-col md:flex-row gap-1 md:opacity-0 md:group-hover:opacity-100 transition-opacity flex-shrink-0">
            <button
              type="button"
              class="w-8 h-8 md:w-7 md:h-7 flex items-center justify-center rounded-lg hover:bg-surface-container active:bg-surface-container"
              aria-label="编辑"
              @click="openEdit(entry)"
            >
              <span class="material-symbols-outlined text-[16px] text-on-surface-variant">edit</span>
            </button>
            <button
              type="button"
              class="w-8 h-8 md:w-7 md:h-7 flex items-center justify-center rounded-lg hover:bg-error-container active:bg-error-container"
              aria-label="删除"
              @click="deleteEntry(entry)"
            >
              <span class="material-symbols-outlined text-[16px] text-error">delete</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <BasePagination :total="total" :page="page" :page-size="PAGE_SIZE" @update:page="onPageChange" />
  </div>

  <!-- Slide Panel -->
  <BaseSlidePanel :show="showPanel" :title="panelTitle" @close="showPanel = false">
    <div class="space-y-4">
      <div v-if="panelError" class="text-xs text-error bg-error-container px-3 py-2 rounded-lg">
        {{ panelError }}
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">分类</label>
        <select
          v-model="form.category"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        >
          <option v-for="cat in categories.slice(1)" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">问题 <span class="text-error">*</span></label>
        <input
          v-model="form.question"
          type="text"
          placeholder="请输入问题描述"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">解决方案 <span class="text-error">*</span></label>
        <textarea
          v-model="form.solution"
          rows="5"
          placeholder="请输入解决方案..."
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 resize-none leading-relaxed"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">标签（逗号分隔）</label>
        <input
          v-model="form.tags"
          type="text"
          placeholder="如：网络, 连接, VPN"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      <div class="flex gap-2 pt-2">
        <button
          type="button"
          class="flex-1 py-2.5 border border-outline rounded-lg text-sm hover:bg-surface-container active:bg-surface-container min-h-[44px]"
          @click="showPanel = false"
        >
          取消
        </button>
        <button
          type="button"
          class="flex-1 py-2.5 bg-primary-500 text-white rounded-lg text-sm hover:bg-primary-600 active:bg-primary-700 disabled:opacity-60 min-h-[44px]"
          :disabled="saving"
          @click="saveEntry"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </BaseSlidePanel>
</template>
