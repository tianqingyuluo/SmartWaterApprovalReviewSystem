<template>
  <div class="sw-page application-list-page">
    <div class="list-heading">
      <div>
        <h1 class="sw-page-title">申请列表</h1>
        <p>演示环境最近申请列表。MVP 暂无账号权限，使用任务 ID 和会话 ID 进入结果页。</p>
      </div>
      <router-link to="/apply" class="sw-btn sw-btn-primary">新建申请</router-link>
    </div>

    <PageCard compact class="filter-card">
      <div class="filter-grid">
        <label class="filter-field wide">
          <span>任务 ID</span>
          <input
            v-model="filterKeyword"
            class="sw-input"
            type="text"
            placeholder="搜索任务 ID"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="filter-field">
          <span>状态</span>
          <select v-model="filterStatus" class="sw-select">
            <option value="">请选择状态</option>
            <option v-for="status in STATUS_OPTIONS" :key="status" :value="status">
              {{ STATUS_LABELS_APPLICANT[status] }}
            </option>
          </select>
        </label>
        <label class="filter-field date-pair">
          <span>提交日期</span>
          <div class="date-inputs">
            <input v-model="filterStartDate" class="sw-input" type="date" />
            <b>→</b>
            <input v-model="filterEndDate" class="sw-input" type="date" />
          </div>
        </label>
        <div class="filter-actions">
          <button type="button" class="sw-btn sw-btn-ghost" @click="handleReset">重置</button>
          <button type="button" class="sw-btn sw-btn-primary" @click="handleSearch">查询</button>
        </div>
      </div>
    </PageCard>

    <PageCard compact class="table-card">
      <div v-if="errorMessage" class="sw-alert sw-alert-danger list-alert">
        {{ errorMessage }}
      </div>

      <div class="table-scroll">
        <table class="application-table">
          <thead>
            <tr>
              <th>任务 ID</th>
              <th>状态</th>
              <th>提交时间</th>
              <th>更新时间</th>
              <th>知识包版本</th>
              <th>材料提交情况</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7">
                <div class="table-loading">
                  <span class="sw-spinner"></span>
                  <span>正在加载申请列表</span>
                </div>
              </td>
            </tr>
            <tr v-else-if="filteredItems.length === 0">
              <td colspan="7">
                <EmptyState
                  title="暂无申请记录"
                  description="当前列表只展示真实后端列表 API 返回的数据。"
                >
                  <router-link to="/apply" class="sw-btn sw-btn-primary">新建申请</router-link>
                </EmptyState>
              </td>
            </tr>
<template v-else>
              <tr v-for="item in paginatedItems" :key="item.taskId">
              <td class="task-id">{{ item.taskId }}</td>
              <td><StatusTag :status="item.status" /></td>
              <td>{{ formatDateTime(item.submittedAt) }}</td>
              <td>{{ formatDateTime(item.updatedAt) }}</td>
              <td>{{ item.knowledgePackVersion || '未返回' }}</td>
              <td><TaskMaterialSummary :slots="item.materials" /></td>
              <td>
                <router-link
                  class="detail-link"
                  :to="`/review?taskId=${item.taskId}&sessionId=${item.sessionId}`"
                >
                  进入详情
                </router-link>
              </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-if="filteredItems.length > 0" class="pagination-bar">
        <span>共 {{ filteredItems.length }} 条</span>
        <div class="pager">
          <button type="button" :disabled="currentPage === 1" @click="currentPage -= 1">‹</button>
          <button
            v-for="page in visiblePages"
            :key="page"
            type="button"
            :class="{ active: page === currentPage }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
          <button type="button" :disabled="currentPage === totalPages" @click="currentPage += 1">›</button>
        </div>
        <select v-model="pageSize" class="sw-select page-size-select">
          <option :value="10">10 条/页</option>
          <option :value="20">20 条/页</option>
          <option :value="50">50 条/页</option>
        </select>
      </div>
    </PageCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getTaskList } from '@/api/task'
import type { ProcessingStatus, TaskListItem } from '@/types'
import { STATUS_LABELS_APPLICANT } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import TaskMaterialSummary from '@/components/business/TaskMaterialSummary.vue'

const STATUS_OPTIONS: ProcessingStatus[] = ['SUBMITTED', 'QUEUED', 'PROCESSING', 'PARTIAL_SUCCESS', 'COMPLETED', 'FAILED']

const loading = ref(false)
const errorMessage = ref('')
const items = ref<TaskListItem[]>([])
const filterKeyword = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterStatus = ref<ProcessingStatus | ''>('')
const currentPage = ref(1)
const pageSize = ref(10)

const filteredItems = computed(() => {
  let result = items.value

  const keyword = filterKeyword.value.trim().toLowerCase()
  if (keyword) {
    result = result.filter((item) => item.taskId.toLowerCase().includes(keyword))
  }

  if (filterStatus.value) {
    result = result.filter((item) => item.status === filterStatus.value)
  }

  if (filterStartDate.value) {
    const start = new Date(filterStartDate.value)
    result = result.filter((item) => new Date(item.submittedAt) >= start)
  }

  if (filterEndDate.value) {
    const end = new Date(filterEndDate.value)
    end.setHours(23, 59, 59, 999)
    result = result.filter((item) => new Date(item.submittedAt) <= end)
  }

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / pageSize.value)))

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredItems.value.slice(start, start + pageSize.value)
})

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  const end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let page = start; page <= end; page += 1) {
    pages.push(page)
  }

  return pages
})

watch([pageSize, filterKeyword, filterStatus, filterStartDate, filterEndDate], () => {
  currentPage.value = 1
})

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value || '未返回'
  }
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function handleSearch() {
  currentPage.value = 1
}

function handleReset() {
  filterKeyword.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterStatus.value = ''
  currentPage.value = 1
}

async function fetchList() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await getTaskList(1, 100)
    items.value = res.data.data.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '申请列表加载失败，请稍后重试。'
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.application-list-page {
  max-width: 1480px;
}

.list-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.list-heading p {
  margin-top: -12px;
  margin-bottom: 22px;
  color: var(--sw-muted);
  line-height: 1.7;
}

.filter-card {
  margin-bottom: 14px;
}

.filter-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1.1fr) minmax(170px, 0.8fr) minmax(360px, 1.35fr) auto;
  align-items: end;
  gap: 16px;
}

.filter-field {
  display: grid;
  gap: 8px;
}

.filter-field span {
  color: #26364f;
  font-weight: 800;
}

.date-inputs,
.filter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-inputs b {
  color: #a4b0c2;
}

.table-card {
  overflow: hidden;
}

.list-alert {
  margin-bottom: 14px;
}

.table-scroll {
  overflow-x: auto;
}

.application-table {
  width: 100%;
  min-width: 1040px;
  border-collapse: collapse;
  font-size: 14px;
}

.application-table thead {
  background: #f4f8fd;
}

.application-table th,
.application-table td {
  border-bottom: 1px solid #edf2f7;
  padding: 15px 14px;
  text-align: left;
  vertical-align: middle;
}

.application-table th {
  color: #2f3f56;
  font-weight: 800;
  white-space: nowrap;
}

.application-table td {
  color: #334155;
}

.application-table tbody tr:not(:first-child):hover,
.application-table tbody tr:hover {
  background: #fbfdff;
}

.task-id {
  color: #14213a;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 13px;
  font-weight: 700;
}

.detail-link {
  color: var(--sw-primary);
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
}

.detail-link:hover {
  color: var(--sw-primary-strong);
}

.table-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px 0;
  color: var(--sw-muted);
}

.pagination-bar {
  display: grid;
  grid-template-columns: 1fr auto auto;
  align-items: center;
  gap: 18px;
  padding-top: 20px;
  color: var(--sw-muted);
}

.pager {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pager button {
  min-width: 34px;
  height: 34px;
  border: 1px solid var(--sw-line);
  border-radius: 7px;
  background: #fff;
  color: #334155;
  font-weight: 700;
}

.pager button.active {
  border-color: var(--sw-primary);
  color: var(--sw-primary);
  box-shadow: 0 6px 16px rgba(22, 119, 255, 0.13);
}

.pager button:disabled {
  color: #c5cfdc;
}

.page-size-select {
  width: 116px;
}

@media (max-width: 1180px) {
  .filter-grid {
    grid-template-columns: 1fr 1fr;
  }

  .date-pair,
  .filter-actions {
    grid-column: span 2;
  }
}

@media (max-width: 760px) {
  .list-heading {
    display: block;
  }

  .filter-grid,
  .pagination-bar {
    grid-template-columns: 1fr;
  }

  .date-pair,
  .filter-actions {
    grid-column: auto;
  }

  .date-inputs,
  .filter-actions,
  .pager {
    flex-wrap: wrap;
  }
}
</style>
