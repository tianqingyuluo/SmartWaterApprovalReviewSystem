<template>
  <div class="sw-page max-w-[1480px]">
    <div class="flex items-start justify-between gap-5 max-md:block">
      <div>
        <h1 class="sw-page-title">AI 知识库与 MCP 演示台</h1>
        <p class="mb-[22px] mt-[-12px] leading-[1.7] text-sw-muted">
          演示模式，非正式审批结论。页面用于 CP2 验收展示知识库检索与材料完整性检查。
        </p>
      </div>
      <button type="button" class="sw-btn sw-btn-ghost" :disabled="statusLoading" @click="loadStatus">
        {{ statusLoading ? '刷新中...' : '刷新状态' }}
      </button>
    </div>

    <div class="mb-4 grid gap-4 [grid-template-columns:repeat(4,minmax(0,1fr))] max-[1180px]:grid-cols-2 max-md:grid-cols-1">
      <PageCard compact>
        <p class="text-sm font-bold text-sw-muted">知识库状态</p>
        <strong class="mt-2 block text-2xl text-[#12213a]">{{ status.knowledgeAvailable ? '可用' : '不可用' }}</strong>
        <span class="mt-2 inline-flex rounded-full bg-[#eef6ff] px-3 py-1 text-xs font-bold text-sw-primary">
          {{ status.knowledgePackVersion }}
        </span>
      </PageCard>
      <PageCard compact>
        <p class="text-sm font-bold text-sw-muted">MCP 服务状态</p>
        <strong class="mt-2 block text-2xl text-[#12213a]">{{ status.mcpAvailable ? '可用' : '不可用' }}</strong>
        <span class="mt-2 inline-flex rounded-full px-3 py-1 text-xs font-bold" :class="status.source === 'api' ? 'bg-[#ecfdf3] text-sw-success' : 'bg-[#fff8e8] text-[#9a6700]'">
          {{ status.source === 'api' ? '真实接口' : '演示数据' }}
        </span>
      </PageCard>
      <PageCard compact>
        <p class="text-sm font-bold text-sw-muted">最近调用工具</p>
        <strong class="mt-2 block text-xl text-[#12213a]">{{ status.lastToolName || '暂无调用' }}</strong>
        <span class="mt-2 block text-sm text-sw-muted">{{ formatDateTime(status.lastCalledAt) }}</span>
      </PageCard>
      <PageCard compact>
        <p class="text-sm font-bold text-sw-muted">演示说明</p>
        <p class="mt-2 leading-[1.7] text-[#34516f]">{{ status.message }}</p>
      </PageCard>
    </div>

    <div class="grid items-start gap-5 [grid-template-columns:minmax(420px,1fr)_minmax(420px,1fr)] max-[1180px]:grid-cols-1">
      <PageCard title="knowledge_search" subtitle="输入查询词，展示知识库命中结果和依据片段。" compact>
        <div class="grid gap-3 [grid-template-columns:minmax(0,1fr)_120px_auto] max-md:grid-cols-1">
          <input v-model="searchQuery" class="sw-input" placeholder="例如：取水许可 材料" @keyup.enter="runKnowledgeSearch" />
          <input v-model.number="searchTopK" class="sw-input" type="number" min="1" max="50" />
          <button type="button" class="sw-btn sw-btn-primary" :disabled="searchLoading" @click="runKnowledgeSearch">
            {{ searchLoading ? '检索中...' : '检索' }}
          </button>
        </div>

        <div class="mt-3 flex flex-wrap gap-3 text-sm">
          <button type="button" class="font-bold text-sw-primary underline" :disabled="searchLoading" @click="runEmptyKnowledgeSearch">
            演示空结果
          </button>
          <button type="button" class="font-bold text-sw-danger underline" :disabled="searchLoading" @click="runFailedKnowledgeSearch">
            演示失败
          </button>
        </div>

        <div v-if="searchValidationError" class="sw-alert sw-alert-warning mt-4">
          {{ searchValidationError }}
        </div>

        <div v-if="searchError" class="sw-alert sw-alert-danger mt-4">
          {{ searchError }}
          <button type="button" class="ml-3 font-bold text-sw-danger underline" @click="runKnowledgeSearch">重试</button>
        </div>

        <div v-if="searchLoading" class="mt-4 flex items-center justify-center gap-2.5 rounded-[10px] bg-[#f6f9fd] py-10 text-sw-muted">
          <span class="sw-spinner"></span>
          <span>正在调用 knowledge_search</span>
        </div>

        <EmptyState
          v-else-if="searchResult && searchResult.results.length === 0"
          title="没有检索结果"
          description="可以换一个查询词，或在真实后端中检查知识库是否完成 ingest。"
        />

        <div v-else-if="searchResult" class="mt-4 grid gap-3">
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-[10px] bg-[#f6f9fd] px-4 py-3">
            <span class="font-bold text-[#26364f]">命中 {{ searchResult.total }} 条</span>
            <code>{{ searchResult.knowledgePackVersion }}</code>
          </div>
          <article
            v-for="item in searchResult.results"
            :key="`${item.rank}-${item.section}-${item.id}`"
            class="rounded-[10px] border border-sw-line bg-white p-4"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <strong class="text-[#12213a]">#{{ item.rank }} {{ item.title }}</strong>
                <p class="mt-1 text-xs text-sw-muted">{{ item.section }} / {{ item.id }}</p>
              </div>
              <span class="rounded-full bg-[#eef6ff] px-3 py-1 text-xs font-bold text-sw-primary">score {{ item.score }}</span>
            </div>
            <p class="mt-3 leading-[1.75] text-[#34516f]">{{ item.excerpt || '该条目未返回依据片段。' }}</p>
            <div class="mt-3 grid gap-2 text-xs text-sw-muted">
              <span v-if="item.materialType">材料：{{ materialLabel(item.materialType) }}</span>
              <span v-if="item.fieldPath">字段：{{ item.fieldPath }}</span>
              <span v-if="item.basisRefs.length">依据：{{ item.basisRefs.join('、') }}</span>
            </div>
          </article>
        </div>
      </PageCard>

      <PageCard title="check_completeness" subtitle="选择已提交材料，展示完整性判断、缺失项和问题提示。" compact>
        <div class="grid gap-3">
          <label
            v-for="slot in MATERIAL_SLOTS"
            :key="slot"
            class="flex min-h-12 items-center justify-between gap-3 rounded-[10px] border border-sw-line bg-white px-4 py-3"
          >
            <span class="font-bold text-[#26364f]">{{ materialLabel(slot) }}</span>
            <input v-model="selectedMaterials" type="checkbox" :value="slot" class="h-5 w-5 accent-[#1677ff]" />
          </label>
          <button type="button" class="sw-btn sw-btn-primary" :disabled="completenessLoading" @click="runCompletenessCheck()">
            {{ completenessLoading ? '检查中...' : '检查完整性' }}
          </button>
        </div>

        <div class="mt-3 flex flex-wrap gap-3 text-sm">
          <button type="button" class="font-bold text-sw-primary underline" :disabled="completenessLoading" @click="runEmptyCompletenessCheck">
            演示空结果
          </button>
          <button type="button" class="font-bold text-sw-danger underline" :disabled="completenessLoading" @click="runFailedCompletenessCheck">
            演示失败
          </button>
        </div>

        <div v-if="completenessValidationError" class="sw-alert sw-alert-warning mt-4">
          {{ completenessValidationError }}
        </div>

        <div v-if="completenessError" class="sw-alert sw-alert-danger mt-4">
          {{ completenessError }}
          <button type="button" class="ml-3 font-bold text-sw-danger underline" @click="runCompletenessCheck()">重试</button>
        </div>

        <div v-if="completenessLoading" class="mt-4 flex items-center justify-center gap-2.5 rounded-[10px] bg-[#f6f9fd] py-10 text-sw-muted">
          <span class="sw-spinner"></span>
          <span>正在调用 check_completeness</span>
        </div>

        <div v-else-if="completenessResult" class="mt-4 grid gap-3">
          <div class="sw-alert" :class="completenessResult.complete ? 'sw-alert-info' : 'sw-alert-warning'">
            <strong>{{ completenessResult.complete ? '材料完整' : '材料不完整' }}</strong>
            <p class="mt-1">已提交 {{ completenessResult.submitted.length }}/{{ completenessResult.required.length }} 项。</p>
          </div>

          <div class="grid gap-2">
            <div
              v-for="type in completenessResult.required"
              :key="type"
              class="flex items-center justify-between rounded-[10px] bg-[#f6f9fd] px-4 py-3"
            >
              <span class="font-bold text-[#26364f]">{{ materialLabel(type) }}</span>
              <span
                class="rounded-full px-3 py-1 text-xs font-bold"
                :class="completenessResult.missing.includes(type) ? 'bg-[#fff2f0] text-sw-danger' : 'bg-[#ecfdf3] text-sw-success'"
              >
                {{ completenessResult.missing.includes(type) ? '缺失' : '已提交' }}
              </span>
            </div>
          </div>

          <EmptyState
            v-if="completenessResult.findings.length === 0"
            title="没有完整性问题"
            description="已提交材料覆盖当前 MVP 必需项，check_completeness 没有返回缺失项。"
          />

          <div v-else class="grid gap-2">
            <article
              v-for="finding in completenessResult.findings"
              :key="`${finding.materialType}-${finding.code}`"
              class="rounded-[10px] border-l-4 border-sw-warning bg-[#fff8e8] px-4 py-3"
            >
              <strong class="text-[#714b00]">{{ finding.code }} / {{ finding.severity }}</strong>
              <p class="mt-1 leading-[1.7] text-[#714b00]">{{ finding.message }}</p>
              <small class="mt-2 block text-[#9a6700]">{{ finding.basisRefs.join('、') }}</small>
            </article>
          </div>
        </div>
      </PageCard>
    </div>

    <PageCard title="接口契约样例" subtitle="供 CP2 验收材料直接引用，请求字段按 Python MCP 工具保持 snake_case 入参。" compact class="mt-5">
      <div class="grid gap-4 [grid-template-columns:repeat(2,minmax(0,1fr))] max-[1180px]:grid-cols-1">
        <div class="min-w-0">
          <h3 class="mb-3 text-base font-black text-[#16233b]">knowledge_search</h3>
          <pre class="overflow-auto rounded-[10px] bg-[#111827] p-4 text-xs leading-[1.7] text-[#dbeafe]">{{ searchContractJson }}</pre>
        </div>
        <div class="min-w-0">
          <h3 class="mb-3 text-base font-black text-[#16233b]">check_completeness</h3>
          <pre class="overflow-auto rounded-[10px] bg-[#111827] p-4 text-xs leading-[1.7] text-[#dbeafe]">{{ completenessContractJson }}</pre>
        </div>
      </div>
    </PageCard>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { buildDemoCompleteness, buildDemoKnowledgeSearch, buildDemoStatus } from '@/api/knowledge'
import type { CompletenessResponse, KnowledgeSearchResponse, KnowledgeStatusView, MaterialType, McpToolName } from '@/types'
import { MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const status = ref<KnowledgeStatusView>(buildDemoStatus())
const statusLoading = ref(false)

const searchQuery = ref('取水许可 材料')
const searchTopK = ref(5)
const searchLoading = ref(false)
const searchValidationError = ref('')
const searchError = ref('')
const searchResult = ref<KnowledgeSearchResponse | null>(null)

const selectedMaterials = ref<MaterialType[]>(['APPLICATION_FORM', 'BUSINESS_LICENSE'])
const completenessLoading = ref(false)
const completenessValidationError = ref('')
const completenessError = ref('')
const completenessResult = ref<CompletenessResponse | null>(null)

const searchContractJson = computed(() => JSON.stringify({
  request: {
    tool: 'knowledge_search',
    body: { query: '取水许可 材料', top_k: 5 },
  },
  response: {
    query: '取水许可 材料',
    topK: 5,
    total: 1,
    results: [{
      rank: 1,
      section: 'materialChecklist',
      id: 'mvp-required-application-form',
      title: '取水许可申请书',
      materialType: 'APPLICATION_FORM',
      excerpt: '依据片段',
      sourceIds: ['water-permit:mvp:application'],
      basisRefs: ['BASIS_APPLICATION_FORM_REQUIRED'],
    }],
    knowledgePackVersion: 'water-permit-mvp-2026-05',
  },
}, null, 2))

const completenessContractJson = computed(() => JSON.stringify({
  request: {
    tool: 'check_completeness',
    body: { materials: ['APPLICATION_FORM', 'BUSINESS_LICENSE'] },
  },
  response: {
    submitted: ['APPLICATION_FORM', 'BUSINESS_LICENSE'],
    required: ['APPLICATION_FORM', 'BUSINESS_LICENSE', 'ID_CARD'],
    missing: ['ID_CARD'],
    complete: false,
    findings: [{
      code: 'MISSING_MATERIAL',
      severity: 'BLOCKER',
      materialType: 'ID_CARD',
      message: '身份证未提交，完整性检查不通过。',
      basisRefs: ['BASIS_MVP_REQUIRED_MATERIALS'],
    }],
    knowledgePackVersion: 'water-permit-mvp-2026-05',
  },
}, null, 2))

onMounted(() => {
  status.value = buildDemoStatus()
  runKnowledgeSearch()
  runCompletenessCheck()
})

function loadStatus() {
  statusLoading.value = true
  status.value = {
    ...status.value,
    lastCalledAt: new Date().toISOString(),
    source: 'demo' as const,
    message: '演示台状态已刷新为本地数据。',
  }
  window.setTimeout(() => {
    statusLoading.value = false
  }, 250)
}

async function runKnowledgeSearch() {
  searchValidationError.value = ''
  searchError.value = ''
  searchResult.value = null

  if (!searchQuery.value.trim()) {
    searchValidationError.value = '请输入查询词后重试。'
    return
  }
  if (!Number.isFinite(searchTopK.value) || searchTopK.value < 1 || searchTopK.value > 50) {
    searchValidationError.value = 'topK 需要在 1-50 之间，请修改后重试。'
    return
  }

  searchLoading.value = true
  try {
    await demoDelay()
    if (searchQuery.value.trim().toLowerCase() === 'simulate-error') {
      throw new Error('knowledge_search 模拟失败，请点击重试。')
    }
    searchResult.value = buildDemoKnowledgeSearch({ query: searchQuery.value, topK: searchTopK.value })
    markToolCall('knowledge_search', '当前使用演示数据，等待后端 MCP HTTP 代理接入。', 'demo')
  } catch (error) {
    searchError.value = error instanceof Error ? error.message : 'knowledge_search 调用失败，请重试。'
  } finally {
    searchLoading.value = false
  }
}

async function runCompletenessCheck(options: { simulateFailure?: boolean } = {}) {
  completenessValidationError.value = ''
  completenessError.value = ''
  completenessResult.value = null

  if (selectedMaterials.value.length === 0) {
    completenessValidationError.value = '请至少选择一项材料后重试。'
    return
  }

  completenessLoading.value = true
  try {
    await demoDelay()
    if (options.simulateFailure) {
      throw new Error('check_completeness 模拟失败，请点击重试。')
    }
    completenessResult.value = buildDemoCompleteness(selectedMaterials.value)
    markToolCall('check_completeness', '当前使用演示数据，等待后端 MCP HTTP 代理接入。', 'demo')
  } catch (error) {
    completenessError.value = error instanceof Error ? error.message : 'check_completeness 调用失败，请重试。'
    markToolCall('check_completeness', 'check_completeness 调用失败，可点击重试。', 'demo')
  } finally {
    completenessLoading.value = false
  }
}

function runEmptyKnowledgeSearch() {
  searchQuery.value = '无匹配演示查询'
  runKnowledgeSearch()
}

function runFailedKnowledgeSearch() {
  searchQuery.value = 'simulate-error'
  runKnowledgeSearch()
}

function runEmptyCompletenessCheck() {
  selectedMaterials.value = [...MATERIAL_SLOTS]
  runCompletenessCheck()
}

function runFailedCompletenessCheck() {
  if (selectedMaterials.value.length === 0) {
    selectedMaterials.value = ['APPLICATION_FORM']
  }
  runCompletenessCheck({ simulateFailure: true })
}

const DEMO_DELAY_MS = 350

function demoDelay() {
  return new Promise((resolve) => window.setTimeout(resolve, DEMO_DELAY_MS))
}

function markToolCall(toolName: McpToolName, message: string, source: 'api' | 'demo') {
  status.value = {
    ...status.value,
    lastToolName: toolName,
    lastCalledAt: new Date().toISOString(),
    source,
    message,
  }
}

function materialLabel(type: MaterialType): string {
  return MATERIAL_LABELS[type]
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return '暂无调用'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
</script>
