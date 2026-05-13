<template>
  <div class="application-list-page">
    <!-- 页面标题栏 -->
    <div class="page-header-bar">
      <h1 class="page-title">取水许可申请列表</h1>
      <router-link to="/apply" class="btn-primary">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        新建申请
      </router-link>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar">
      <div class="filter-group">
        <input
          v-model="filterKeyword"
          type="text"
          class="filter-input"
          placeholder="请输入申请编号"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="filter-group date-range">
        <input v-model="filterStartDate" type="date" class="filter-input date-input"/>
        <span class="date-separator">~</span>
        <input v-model="filterEndDate" type="date" class="filter-input date-input"/>
      </div>
      <div class="filter-group">
        <select v-model="filterStatus" class="filter-select">
          <option value="">选择状态</option>
          <option v-for="s in STATUS_OPTIONS" :key="s" :value="s">
            {{ STATUS_LABELS_APPLICANT[s] }}
          </option>
        </select>
      </div>
      <button class="btn-primary" @click="handleSearch">
        查询
      </button>
      <button class="btn-default" @click="handleReset">
        重置
      </button>
    </div>

    <!-- 表格区 -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>申请编号</th>
            <th>提交时间</th>
            <th>状态</th>
            <th>材料情况</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="loading-cell">
              <div class="loading-spinner"></div>
              加载中...
            </td>
          </tr>
          <tr v-else-if="filteredItems.length === 0">
            <td colspan="5" class="empty-cell">
              <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d9d9d9" stroke-width="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <p>暂无申请记录</p>
                <router-link to="/apply" class="link-primary">点击新建申请开始</router-link>
              </div>
            </td>
          </tr>
          <tr
            v-for="item in paginatedItems"
            :key="item.taskId"
            class="data-row"
          >
            <td class="task-id">{{ item.taskId }}</td>
            <td>{{ formatDateTime(item.submittedAt) }}</td>
            <td>
              <StatusTag :status="item.status" />
            </td>
            <td>
              <div class="material-dots">
                <span
                  v-for="slot in item.materials"
                  :key="slot.materialType"
                  class="material-dot"
                  :class="{ uploaded: slot.uploaded }"
                  :title="MATERIAL_LABELS[slot.materialType] + (slot.uploaded ? '（已上传）' : '（未上传）')"
                >
                  {{ MATERIAL_LABELS[slot.materialType]?.charAt(0) }}
                </span>
              </div>
            </td>
            <td>
              <router-link
                :to="`/review?taskId=${item.taskId}&sessionId=${item.sessionId}`"
                class="link-action"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                查看
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div v-if="filteredItems.length > 0" class="pagination-bar">
      <span class="total-text">共 {{ filteredItems.length }} 条</span>
      <div class="page-controls">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          &lt;
        </button>
        <button
          v-for="page in visiblePages"
          :key="page"
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          &gt;
        </button>
      </div>
      <select v-model="pageSize" class="page-size-select">
        <option :value="10">10条/页</option>
        <option :value="20">20条/页</option>
        <option :value="50">50条/页</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getTaskList } from '@/api/task'
import type { TaskListItem, ProcessingStatus } from '@/types'
import { STATUS_LABELS_APPLICANT, MATERIAL_LABELS } from '@/types'
import StatusTag from '@/components/common/StatusTag.vue'

const STATUS_OPTIONS: ProcessingStatus[] = ['SUBMITTED', 'QUEUED', 'PROCESSING', 'PARTIAL_SUCCESS', 'COMPLETED', 'FAILED']

const loading = ref(false)
const items = ref<TaskListItem[]>([])
const filterKeyword = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const filteredItems = computed(() => {
  let result = items.value

  if (filterKeyword.value) {
    const kw = filterKeyword.value.toLowerCase()
    result = result.filter((item) => item.taskId.toLowerCase().includes(kw))
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
  const end = start + pageSize.value
  return filteredItems.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

watch(pageSize, () => {
  currentPage.value = 1
})

function formatDateTime(dt: string): string {
  const d = new Date(dt)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function handleSearch() {
  currentPage.value = 1
  fetchList()
}

function handleReset() {
  filterKeyword.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  filterStatus.value = ''
  currentPage.value = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getTaskList(1, 100)
    items.value = res.data.data.items
  } catch (e) {
    console.error('获取申请列表失败', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.application-list-page {
  max-width: 1200px;
}

.page-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-default {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: #fff;
  color: #666;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-default:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
}

.filter-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  width: 200px;
  transition: border-color 0.2s;
}

.filter-input:focus {
  outline: none;
  border-color: #1890ff;
}

.filter-input::placeholder {
  color: #bbb;
}

.date-input {
  width: 130px;
}

.date-separator {
  margin: 0 8px;
  color: #999;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  width: 130px;
  background: #fff;
  cursor: pointer;
}

.table-wrapper {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table thead {
  background: #fafafa;
}

.data-table th {
  padding: 14px 16px;
  text-align: left;
  font-weight: 500;
  color: #666;
  border-bottom: 1px solid #e8e8e8;
  white-space: nowrap;
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
}

.data-row:hover {
  background: #f5f7fa;
}

.task-id {
  font-family: monospace;
  font-size: 13px;
}

.material-dots {
  display: flex;
  gap: 6px;
}

.material-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #f5f5f5;
  color: #bbb;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e0e0e0;
  cursor: help;
}

.material-dot.uploaded {
  background: #f6ffed;
  color: #52c41a;
  border-color: #b7eb8f;
}

.link-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #1890ff;
  text-decoration: none;
  font-size: 13px;
  cursor: pointer;
}

.link-action:hover {
  color: #40a9ff;
}

.link-primary {
  color: #1890ff;
  text-decoration: none;
}

.link-primary:hover {
  color: #40a9ff;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 60px 16px;
  color: #999;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #f0f0f0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-state p {
  margin: 0;
  color: #999;
}

.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding: 0 8px;
}

.total-text {
  font-size: 14px;
  color: #666;
}

.page-controls {
  display: flex;
  gap: 4px;
}

.page-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: 4px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-btn:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}

.page-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-size-select {
  padding: 6px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
}
</style>
