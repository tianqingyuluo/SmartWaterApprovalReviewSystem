<template>
  <div class="sw-page max-w-[1480px]">
    <div class="flex items-start justify-between gap-5 max-md:block">
      <div>
        <h1 class="sw-page-title">申请列表</h1>
        <p class="mb-[22px] mt-[-12px] leading-[1.7] text-sw-muted">
          演示环境最近申请列表。MVP 暂无账号权限，使用任务 ID 和会话 ID 进入结果页。
        </p>
      </div>
      <router-link to="/apply" class="sw-btn sw-btn-primary">新建申请</router-link>
    </div>

    <PageCard compact class="mb-[14px]">
      <div class="grid items-end gap-4 max-[1180px]:grid-cols-2 max-md:grid-cols-1 [grid-template-columns:minmax(220px,1.1fr)_minmax(170px,0.8fr)_minmax(360px,1.35fr)_auto]">
        <label class="grid gap-2">
          <span class="font-extrabold text-[#26364f]">任务 ID</span>
          <input
            v-model="filterKeyword"
            class="sw-input"
            type="text"
            placeholder="搜索任务 ID"
            @keyup.enter="handleSearch"
          />
        </label>
        <label class="grid gap-2">
          <span class="font-extrabold text-[#26364f]">状态</span>
          <select v-model="filterStatus" class="sw-select">
            <option value="">请选择状态</option>
            <option v-for="status in STATUS_OPTIONS" :key="status" :value="status">
              {{ STATUS_LABELS_APPLICANT[status] }}
            </option>
          </select>
        </label>
        <label class="grid gap-2 max-[1180px]:col-span-2 max-md:col-auto">
          <span class="font-extrabold text-[#26364f]">提交日期</span>
          <div class="flex items-center gap-3 max-md:flex-wrap">
            <input v-model="filterStartDate" class="sw-input" type="date" />
            <b class="text-[#a4b0c2]">→</b>
            <input v-model="filterEndDate" class="sw-input" type="date" />
          </div>
        </label>
        <div class="flex items-center gap-3 max-[1180px]:col-span-2 max-md:col-auto max-md:flex-wrap">
          <button type="button" class="sw-btn sw-btn-ghost" @click="handleReset">重置</button>
          <button type="button" class="sw-btn sw-btn-primary" @click="handleSearch">查询</button>
        </div>
      </div>
    </PageCard>

    <PageCard compact class="overflow-hidden">
      <div v-if="errorMessage" class="sw-alert sw-alert-danger mb-[14px]">
        {{ errorMessage }}
      </div>

      <div class="overflow-x-auto">
        <table class="min-w-[1040px] w-full border-collapse text-sm">
          <thead class="bg-[#f4f8fd]">
            <tr>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">任务 ID</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">状态</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">提交时间</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">更新时间</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">知识包版本</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">材料提交情况</th>
              <th class="whitespace-nowrap border-b border-[#edf2f7] px-[14px] py-[15px] text-left font-extrabold text-[#2f3f56]">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7">
                <div class="flex items-center justify-center gap-2.5 py-12 text-sw-muted">
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
              <tr
                v-for="item in paginatedItems"
                :key="item.taskId"
                class="border-b border-[#edf2f7] align-middle text-slate-700 hover:bg-[#fbfdff]"
              >
                <td class="px-[14px] py-[15px] font-mono text-[13px] font-bold text-[#14213a]">{{ item.taskId }}</td>
                <td class="px-[14px] py-[15px]"><StatusTag :status="item.status" /></td>
                <td class="px-[14px] py-[15px]">{{ formatDateTime(item.submittedAt) }}</td>
                <td class="px-[14px] py-[15px]">{{ formatDateTime(item.updatedAt) }}</td>
                <td class="px-[14px] py-[15px]">{{ item.knowledgePackVersion || '未返回' }}</td>
                <td class="px-[14px] py-[15px]"><TaskMaterialSummary :slots="item.materials" /></td>
                <td class="px-[14px] py-[15px]">
                  <router-link
                    class="whitespace-nowrap font-extrabold text-sw-primary no-underline hover:text-sw-primary-strong"
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

      <div
        v-if="filteredItems.length > 0"
        class="grid items-center gap-[18px] pt-5 text-sw-muted max-md:grid-cols-1 [grid-template-columns:1fr_auto_auto]"
      >
        <span>共 {{ filteredItems.length }} 条</span>
        <div class="flex items-center gap-2 max-md:flex-wrap">
          <button
            type="button"
            :disabled="currentPage === 1"
            class="h-[34px] min-w-[34px] rounded-[7px] border border-sw-line bg-white font-bold text-slate-700 disabled:text-[#c5cfdc]"
            @click="currentPage -= 1"
          >
            ‹
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            type="button"
            :class="
              page === currentPage
                ? 'border-sw-primary text-sw-primary shadow-[0_6px_16px_rgba(22,119,255,0.13)]'
                : 'border-sw-line text-slate-700'
            "
            class="h-[34px] min-w-[34px] rounded-[7px] border bg-white font-bold disabled:text-[#c5cfdc]"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
          <button
            type="button"
            :disabled="currentPage === totalPages"
            class="h-[34px] min-w-[34px] rounded-[7px] border border-sw-line bg-white font-bold text-slate-700 disabled:text-[#c5cfdc]"
            @click="currentPage += 1"
          >
            ›
          </button>
        </div>
        <select v-model="pageSize" class="sw-select w-[116px]">
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
