<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { accountsApi } from '@/api/accounts'
import { useAuthStore } from '@/stores/auth'
import BasePagination from '@/components/BasePagination.vue'
import BaseSlidePanel from '@/components/BaseSlidePanel.vue'
import {
  ACCOUNT_ROLE,
  ACCOUNT_STATUS,
  ACCOUNT_DEPARTMENTS,
  ACCOUNT_DEPARTMENT_LABELS,
  fmtDate,
} from '@/utils/constants'

const auth = useAuthStore()

const standardDepartmentValues = new Set(
  ACCOUNT_DEPARTMENTS.map((d) => d.value).filter(Boolean),
)

function departmentTableLabel(code) {
  if (!code) return '—'
  return ACCOUNT_DEPARTMENT_LABELS[code] ?? code
}

const departmentSelectOptions = computed(() => {
  const opts = [...ACCOUNT_DEPARTMENTS]
  const d = form.department
  if (d && !standardDepartmentValues.has(d)) {
    return [{ value: d, label: `${d}（历史）` }, ...opts]
  }
  return opts
})

const accounts = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const PAGE_SIZE = 10

const searchName = ref('')
const statusFilter = ref('')

const showPanel = ref(false)
const editingAccount = ref(null)
const saving = ref(false)
const panelError = ref('')

const form = reactive({
  employee_id: '',
  username: '',
  name: '',
  password: '',
  department: '',
  email: '',
  phone: '',
  role: 'user',
})

async function loadAccounts() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: PAGE_SIZE }
    if (searchName.value) params.name = searchName.value
    if (statusFilter.value) params.status = statusFilter.value
    const data = await accountsApi.list(params)
    accounts.value = data?.items ?? []
    total.value = data?.total ?? 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAccounts)

let searchTimer
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadAccounts() }, 400)
}

function onPageChange(p) {
  page.value = p
  loadAccounts()
}

function openCreate() {
  editingAccount.value = null
  Object.assign(form, {
    employee_id: '', username: '', name: '', password: '',
    department: '', email: '', phone: '', role: 'user',
  })
  panelError.value = ''
  showPanel.value = true
}

function openEdit(account) {
  editingAccount.value = account
  Object.assign(form, {
    employee_id: account.employee_id,
    username: account.username,
    name: account.name,
    password: '',
    department: account.department ?? '',
    email: account.email ?? '',
    phone: account.phone ?? '',
    role: account.role,
  })
  panelError.value = ''
  showPanel.value = true
}

async function saveAccount() {
  if (!editingAccount.value && (!form.username || !form.password)) {
    panelError.value = '用户名和密码不能为空'
    return
  }
  saving.value = true
  panelError.value = ''
  try {
    if (editingAccount.value) {
      const payload = {
        name: form.name,
        email: form.email,
        phone: form.phone,
        role: form.role,
      }
      const prevDept = editingAccount.value.department ?? ''
      const nextDept = form.department ?? ''
      if (nextDept !== prevDept) {
        payload.department = nextDept === '' ? null : nextDept
      }
      await accountsApi.update(editingAccount.value.id, payload)
    } else {
      await accountsApi.create({
        username: form.username,
        name: form.name,
        password: form.password,
        department: form.department || null,
        email: form.email || null,
        phone: form.phone || null,
        role: form.role,
      })
    }
    showPanel.value = false
    await loadAccounts()
  } catch (e) {
    panelError.value = e.message
  } finally {
    saving.value = false
  }
}

async function toggleFreeze(account) {
  const action = account.status === 'active' ? '冻结' : '解冻'
  if (!confirm(`确认${action}账号「${account.name}」？`)) return
  try {
    if (account.status === 'active') {
      await accountsApi.freeze(account.id)
    } else {
      await accountsApi.unfreeze(account.id)
    }
    await loadAccounts()
  } catch (e) {
    alert(`${action}失败：${e.message}`)
  }
}

const panelTitle = () => (editingAccount.value ? '编辑账号' : '新建账号')
</script>

<template>
  <div class="p-4 md:p-6 space-y-4">
    <!-- Filter bar -->
    <div class="ops-card flex flex-col md:flex-row md:flex-wrap md:items-center md:justify-between gap-3 p-3 md:p-4">
      <div class="flex flex-col sm:flex-row sm:items-center gap-2 flex-1 min-w-0">
        <div class="relative flex-1 min-w-0">
          <span class="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[16px] text-on-surface-variant pointer-events-none">
            search
          </span>
          <input
            v-model="searchName"
            type="text"
            placeholder="搜索姓名..."
            class="w-full sm:w-56 pl-8 pr-3 py-2 text-xs ops-input"
            @input="onSearchInput"
          />
        </div>
        <select
          v-model="statusFilter"
          class="w-full sm:w-auto text-xs ops-input px-3 py-2 bg-white cursor-pointer"
          @change="page = 1; loadAccounts()"
        >
          <option value="">全部状态</option>
          <option value="active">正常</option>
          <option value="frozen">已冻结</option>
        </select>
      </div>
      <button
        v-if="auth.isAdmin"
        type="button"
        class="flex items-center justify-center gap-1.5 px-3 py-2 bg-primary-500 text-white text-xs font-medium rounded-lg hover:bg-primary-600 active:bg-primary-700 shadow-sm hover:shadow transition-shadow min-h-[40px] flex-shrink-0"
        @click="openCreate"
      >
        <span class="material-symbols-outlined text-[14px]">person_add</span>
        新建账号
      </button>
    </div>

    <!-- Table (PC ≥ md) -->
    <div class="hidden md:block ops-card overflow-hidden">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b border-outline bg-surface-dim">
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">姓名</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">用户名</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">工号</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">部门</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">角色</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">状态</th>
            <th class="text-left px-4 py-3 font-medium text-on-surface-variant">最后登录</th>
            <th v-if="auth.isAdmin" class="text-right px-4 py-3 font-medium text-on-surface-variant">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="text-center py-12 text-on-surface-variant">加载中...</td>
          </tr>
          <tr v-else-if="accounts.length === 0">
            <td colspan="8" class="text-center py-12 text-on-surface-variant">暂无数据</td>
          </tr>
          <tr
            v-for="account in accounts"
            :key="account.id"
            class="border-b border-outline hover:bg-surface-dim transition-colors"
          >
            <td class="px-4 py-3 font-medium text-on-surface">{{ account.name }}</td>
            <td class="px-4 py-3 text-on-surface-variant">{{ account.username }}</td>
            <td class="px-4 py-3 font-mono text-on-surface-variant">{{ account.employee_id }}</td>
            <td class="px-4 py-3 text-on-surface-variant">{{ departmentTableLabel(account.department) }}</td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 rounded-full font-medium"
                :class="ACCOUNT_ROLE[account.role]?.class"
              >
                {{ ACCOUNT_ROLE[account.role]?.label }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 rounded-full font-medium"
                :class="ACCOUNT_STATUS[account.status]?.class"
              >
                {{ ACCOUNT_STATUS[account.status]?.label }}
              </span>
            </td>
            <td class="px-4 py-3 text-on-surface-variant">{{ fmtDate(account.last_login_at) }}</td>
            <td v-if="auth.isAdmin" class="px-4 py-3 text-right">
              <div class="flex items-center justify-end gap-1">
                <button
                  type="button"
                  class="w-7 h-7 flex items-center justify-center rounded hover:bg-surface-container"
                  title="编辑"
                  @click="openEdit(account)"
                >
                  <span class="material-symbols-outlined text-[16px] text-on-surface-variant">edit</span>
                </button>
                <button
                  type="button"
                  class="w-7 h-7 flex items-center justify-center rounded"
                  :class="account.status === 'active' ? 'hover:bg-error-container' : 'hover:bg-success-container'"
                  :title="account.status === 'active' ? '冻结' : '解冻'"
                  @click="toggleFreeze(account)"
                >
                  <span
                    class="material-symbols-outlined text-[16px]"
                    :class="account.status === 'active' ? 'text-error' : 'text-success'"
                  >
                    {{ account.status === 'active' ? 'lock' : 'lock_open' }}
                  </span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Card list (Mobile < md) -->
    <div class="md:hidden space-y-3">
      <div v-if="loading" class="text-center py-12 text-xs text-on-surface-variant">加载中...</div>
      <div v-else-if="accounts.length === 0" class="text-center py-12 text-xs text-on-surface-variant">暂无数据</div>
      <div
        v-for="account in accounts"
        :key="account.id"
        class="ops-card p-3.5 active:bg-surface-dim transition-colors"
      >
        <!-- 头部：姓名 + 状态徽章 -->
        <div class="flex items-start justify-between gap-2 mb-2">
          <div class="flex items-center gap-2 min-w-0">
            <div
              class="w-9 h-9 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center shrink-0"
            >
              <span class="text-primary-800 text-xs font-semibold">
                {{ account.name?.charAt(0) ?? account.username?.charAt(0) ?? '?' }}
              </span>
            </div>
            <div class="min-w-0">
              <p class="text-sm font-medium text-on-surface truncate">{{ account.name || account.username }}</p>
              <p class="text-[11px] text-on-surface-variant truncate">@{{ account.username }}</p>
            </div>
          </div>
          <span
            class="text-[10px] px-2 py-0.5 rounded-full font-medium flex-shrink-0"
            :class="ACCOUNT_STATUS[account.status]?.class"
          >
            {{ ACCOUNT_STATUS[account.status]?.label }}
          </span>
        </div>

        <!-- 信息网格 -->
        <div class="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px] mb-2 pb-2 border-b border-outline-variant">
          <div class="min-w-0">
            <span class="text-on-surface-variant">工号 </span>
            <span class="font-mono text-on-surface truncate">{{ account.employee_id || '—' }}</span>
          </div>
          <div class="min-w-0">
            <span class="text-on-surface-variant">角色 </span>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
              :class="ACCOUNT_ROLE[account.role]?.class"
            >
              {{ ACCOUNT_ROLE[account.role]?.label }}
            </span>
          </div>
          <div class="min-w-0">
            <span class="text-on-surface-variant">部门 </span>
            <span class="text-on-surface">{{ departmentTableLabel(account.department) }}</span>
          </div>
          <div class="min-w-0">
            <span class="text-on-surface-variant">登录 </span>
            <span class="text-on-surface-variant">{{ fmtDate(account.last_login_at) || '—' }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="auth.isAdmin" class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border border-outline text-on-surface-variant hover:bg-surface-container active:bg-surface-container min-h-[36px]"
            @click="openEdit(account)"
          >
            <span class="material-symbols-outlined text-[14px]">edit</span>
            编辑
          </button>
          <button
            type="button"
            class="flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg border min-h-[36px]"
            :class="account.status === 'active'
              ? 'border-error/30 text-error hover:bg-error-container active:bg-error-container'
              : 'border-success/30 text-success hover:bg-success-container active:bg-success-container'"
            @click="toggleFreeze(account)"
          >
            <span class="material-symbols-outlined text-[14px]">
              {{ account.status === 'active' ? 'lock' : 'lock_open' }}
            </span>
            {{ account.status === 'active' ? '冻结' : '解冻' }}
          </button>
        </div>
      </div>
    </div>

    <BasePagination :total="total" :page="page" :page-size="PAGE_SIZE" @update:page="onPageChange" />
  </div>

  <!-- Slide Panel -->
  <BaseSlidePanel :show="showPanel" :title="panelTitle()" @close="showPanel = false">
    <div class="space-y-4">
      <div v-if="panelError" class="text-xs text-error bg-error-container px-3 py-2 rounded-lg">
        {{ panelError }}
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-on-surface-variant mb-1.5">工号</label>
          <input
            v-if="editingAccount"
            v-model="form.employee_id"
            type="text"
            disabled
            class="w-full border border-outline rounded-lg px-3 py-2 text-sm bg-surface-container text-on-surface-variant"
          />
          <div
            v-else
            class="border border-outline rounded-lg px-3 py-2 text-xs text-on-surface-variant leading-relaxed bg-surface-dim"
          >
            保存时按所选角色自动生成：管理员 <span class="font-mono">ADM#####</span>、运维
            <span class="font-mono">OPS#####</span>、普通用户 <span class="font-mono">USR#####</span>
          </div>
        </div>
        <div>
          <label class="block text-xs font-medium text-on-surface-variant mb-1.5">用户名 <span class="text-error">*</span></label>
          <input
            v-model="form.username"
            type="text"
            :disabled="!!editingAccount"
            class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 disabled:bg-surface-container"
          />
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">姓名</label>
        <input
          v-model="form.name"
          type="text"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">
          密码 {{ editingAccount ? '（留空不修改）' : '*' }}
        </label>
        <input
          v-model="form.password"
          type="password"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-medium text-on-surface-variant mb-1.5">部门</label>
          <select
            v-model="form.department"
            class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500 bg-white"
          >
            <option
              v-for="opt in departmentSelectOptions"
              :key="opt.value === '' ? '_empty' : opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-on-surface-variant mb-1.5">角色</label>
          <select
            v-model="form.role"
            class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
          >
            <option value="user">普通用户</option>
            <option value="operator">运维</option>
            <option value="admin">管理员</option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">邮箱</label>
        <input
          v-model="form.email"
          type="email"
          class="w-full border border-outline rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
        />
      </div>

      <div>
        <label class="block text-xs font-medium text-on-surface-variant mb-1.5">手机</label>
        <input
          v-model="form.phone"
          type="text"
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
          @click="saveAccount"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </BaseSlidePanel>
</template>
