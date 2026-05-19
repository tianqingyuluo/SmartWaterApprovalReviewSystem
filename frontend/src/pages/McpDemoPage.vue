<template>
  <div class="sw-page mx-auto grid max-w-[1480px] gap-5">
    <section class="overflow-hidden rounded-sw border border-sw-line bg-[#0e1f3d] text-white shadow-sw-card">
      <div class="grid gap-5 px-7 py-6 max-lg:grid-cols-1 md:[grid-template-columns:minmax(0,1fr)_auto]">
        <div class="min-w-0">
          <div class="mb-3 flex flex-wrap gap-2">
            <span class="rounded-full bg-white/12 px-3 py-1 text-xs font-bold text-[#cce0ff]">CP2 演示台</span>
            <span class="rounded-full bg-[#ffdf8c] px-3 py-1 text-xs font-black text-[#593900]">演示模式 / 非正式审批结论</span>
          </div>
          <h1 class="text-[28px] font-black leading-tight max-md:text-[22px]">AI 知识库与 MCP 工具演示</h1>
          <p class="mt-3 max-w-[760px] leading-[1.75] text-[#c8d7ef]">
            独立演示 knowledge_search 和 check_completeness 两个工具的调用、状态和结构化结果，不进入 CP3 审批待办链路。
          </p>
        </div>
        <div class="grid min-w-[280px] gap-2 rounded-[10px] border border-white/12 bg-white/8 p-4">
          <span class="text-xs font-bold text-[#a9c5ee]">最近一次调用</span>
          <strong class="text-lg">{{ lastCallLabel }}</strong>
          <span class="text-sm text-[#c8d7ef]">{{ status.lastCalledAt ? formatDateTime(status.lastCalledAt) : '尚未调用工具' }}</span>
        </div>
      </div>
    </section>

    <section class="grid gap-4 md:[grid-template-columns:repeat(4,minmax(0,1fr))]">
      <article class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-soft">
        <span class="text-xs font-bold text-sw-muted">知识库状态</span>
        <div class="mt-3 flex items-center justify-between gap-3">
          <strong class="text-lg text-[#1d2d44]">{{ statusLabel(status.knowledgePackStatus) }}</strong>
          <span class="h-3 w-3 rounded-full" :class="statusDotClass(status.knowledgePackStatus)"></span>
        </div>
        <p class="mt-2 text-sm leading-[1.6] text-sw-muted">{{ status.knowledgePackVersion }}</p>
      </article>
      <article class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-soft">
        <span class="text-xs font-bold text-sw-muted">MCP 服务</span>
        <div class="mt-3 flex items-center justify-between gap-3">
          <strong class="text-lg text-[#1d2d44]">{{ statusLabel(status.mcpStatus) }}</strong>
          <span class="h-3 w-3 rounded-full" :class="statusDotClass(status.mcpStatus)"></span>
        </div>
        <p class="mt-2 text-sm leading-[1.6] text-sw-muted">HTTP 适配路径：/mcp/tools/*</p>
      </article>
      <article class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-soft">
        <span class="text-xs font-bold text-sw-muted">材料完整性</span>
        <div class="mt-3 flex items-center justify-between gap-3">
          <strong class="text-lg text-[#1d2d44]">{{ completenessResult?.complete ? '完整' : '可检查' }}</strong>
          <span class="text-sm font-bold" :class="completenessResult?.complete ? 'text-sw-success' : 'text-sw-warning'">
            {{ completenessResult ? `${completenessResult.missing.length} 项缺失` : '未调用' }}
          </span>
        </div>
        <p class="mt-2 text-sm leading-[1.6] text-sw-muted">固定 MVP 三类材料。</p>
      </article>
      <article class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-soft">
        <span class="text-xs font-bold text-sw-muted">结果来源</span>
        <div class="mt-3 flex items-center justify-between gap-3">
          <strong class="text-lg text-[#1d2d44]">{{ sourceLabel(status.lastSource) }}</strong>
          <span class="rounded-full bg-[#eef6ff] px-2.5 py-1 text-xs font-bold text-sw-primary">{{ status.lastToolName ?? 'none' }}</span>
        </div>
        <p class="mt-2 text-sm leading-[1.6] text-sw-muted">服务不可用时可进入本地演示数据。</p>
      </article>
    </section>

    <section v-if="status.lastError" class="sw-alert sw-alert-warning">
      {{ status.lastError }}
    </section>

    <div class="grid items-start gap-5 xl:[grid-template-columns:minmax(0,1.05fr)_minmax(420px,0.95fr)]">
      <section class="grid gap-5">
        <section class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-card">
          <div class="mb-5 flex items-start justify-between gap-4 max-md:block">
            <div>
              <h2 class="text-[18px] font-black text-[#17243a]">knowledge_search</h2>
              <p class="mt-1.5 leading-[1.65] text-sw-muted">输入查询词和 topK，查看知识片段、依据引用和来源 ID。</p>
            </div>
            <label class="mt-1 flex items-center gap-2 text-sm font-bold text-sw-muted max-md:mt-3">
              <input v-model="allowDemoFallback" type="checkbox" class="h-4 w-4 accent-[#1677ff]" />
              允许演示数据兜底
            </label>
          </div>

          <div class="grid gap-3 md:[grid-template-columns:minmax(0,1fr)_120px_auto]">
            <input v-model="searchQuery" class="sw-input" placeholder="例如：营业执照、取水许可、计划取水量" @keyup.enter="runSearch" />
            <input v-model.number="topK" class="sw-input" type="number" min="1" max="50" />
            <button type="button" class="sw-btn sw-btn-primary" :disabled="searchLoading" @click="runSearch">
              {{ searchLoading ? '检索中' : '检索' }}
            </button>
          </div>

          <div v-if="searchError" class="sw-alert sw-alert-danger mt-4">
            {{ searchError }}
          </div>

          <div v-if="searchLoading" class="mt-5 flex items-center gap-2.5 rounded-[10px] bg-[#f5f9ff] px-4 py-5 text-sw-muted">
            <span class="sw-spinner"></span>
            <span>正在调用 knowledge_search</span>
          </div>

          <EmptyState
            v-else-if="searchResult && searchResult.results.length === 0"
            title="未检索到结果"
            description="可以换用材料类型、字段名或审查依据关键词再试。"
          />

          <div v-else-if="searchResult" class="mt-5 grid gap-3">
            <div class="flex flex-wrap items-center justify-between gap-3 rounded-[10px] bg-[#f6f9fd] px-4 py-3">
              <span class="font-bold text-[#26364f]">返回 {{ searchResult.total }} 条，实际 topK {{ searchResult.topK }}</span>
              <span class="rounded-full px-2.5 py-1 text-xs font-bold" :class="sourceBadgeClass(searchResult.source)">
                {{ sourceLabel(searchResult.source) }}
              </span>
            </div>
            <article
              v-for="item in searchResult.results"
              :key="item.id"
              class="grid gap-3 rounded-[10px] border border-sw-line bg-white p-4"
            >
              <div class="flex flex-wrap items-center gap-2">
                <span class="grid h-7 w-7 place-items-center rounded-full bg-[#eef6ff] text-xs font-black text-sw-primary">{{ item.rank }}</span>
                <strong class="text-[#17243a]">{{ item.title }}</strong>
                <span class="rounded-full bg-[#f4f8fd] px-2 py-1 text-xs font-bold text-sw-muted">{{ item.sectionLabel }}</span>
                <span v-if="item.materialType" class="rounded-full bg-[#fff8e8] px-2 py-1 text-xs font-bold text-[#9a6700]">
                  {{ MATERIAL_LABELS[item.materialType] }}
                </span>
              </div>
              <p class="leading-[1.75] text-[#405574]">{{ item.excerpt || '该片段未返回摘要。' }}</p>
              <div class="grid gap-2 text-xs text-sw-muted md:[grid-template-columns:repeat(3,minmax(0,1fr))]">
                <span class="[overflow-wrap:anywhere]">basisRefs: {{ listText(item.basisRefs) }}</span>
                <span class="[overflow-wrap:anywhere]">sourceIds: {{ listText(item.sourceIds) }}</span>
                <span class="[overflow-wrap:anywhere]">fieldPath: {{ item.fieldPath || '无' }}</span>
              </div>
            </article>
          </div>

          <EmptyState
            v-else
            title="等待检索"
            description="输入查询词后可演示知识库片段检索、引用依据和空结果状态。"
          />
        </section>

        <section class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-card">
          <div class="mb-5">
            <h2 class="text-[18px] font-black text-[#17243a]">check_completeness</h2>
            <p class="mt-1.5 leading-[1.65] text-sw-muted">勾选已提交材料，查看完整性判断、缺失项和结构化问题提示。</p>
          </div>

          <div class="grid gap-3 md:grid-cols-3">
            <label
              v-for="material in MATERIAL_SLOTS"
              :key="material"
              class="flex min-h-[74px] cursor-pointer items-center gap-3 rounded-[10px] border p-4 transition"
              :class="selectedMaterials.includes(material) ? 'border-sw-primary bg-[#f1f7ff]' : 'border-sw-line bg-white hover:border-[#9cc5ff]'"
            >
              <input v-model="selectedMaterials" type="checkbox" class="h-4 w-4 accent-[#1677ff]" :value="material" />
              <span class="font-bold text-[#26364f]">{{ MATERIAL_LABELS[material] }}</span>
            </label>
          </div>

          <div class="mt-4 flex flex-wrap gap-3">
            <button type="button" class="sw-btn sw-btn-primary" :disabled="completenessLoading" @click="runCompleteness">
              {{ completenessLoading ? '检查中' : '检查完整性' }}
            </button>
            <button type="button" class="sw-btn sw-btn-ghost" @click="selectAllMaterials">全选材料</button>
            <button type="button" class="sw-btn sw-btn-ghost" @click="selectedMaterials = []">清空</button>
          </div>

          <div v-if="completenessError" class="sw-alert sw-alert-danger mt-4">
            {{ completenessError }}
          </div>

          <div v-if="completenessLoading" class="mt-5 flex items-center gap-2.5 rounded-[10px] bg-[#f5f9ff] px-4 py-5 text-sw-muted">
            <span class="sw-spinner"></span>
            <span>正在调用 check_completeness</span>
          </div>

          <div v-else-if="completenessResult" class="mt-5 grid gap-4">
            <div
              class="rounded-[10px] border px-4 py-4"
              :class="completenessResult.complete ? 'border-[#bdebd3] bg-[#f1fbf6]' : 'border-[#ffe1a6] bg-[#fff8e8]'"
            >
              <strong :class="completenessResult.complete ? 'text-[#087443]' : 'text-[#9a6700]'">
                {{ completenessResult.complete ? '材料完整，可进入后续演示' : `缺失 ${completenessResult.missing.length} 项材料` }}
              </strong>
              <p class="mt-2 leading-[1.7] text-sw-muted">
                已识别：{{ materialListText(completenessResult.submitted) }}；缺失：{{ materialListText(completenessResult.missing) }}
              </p>
            </div>

            <div v-if="completenessResult.findings.length" class="grid gap-3">
              <article
                v-for="finding in completenessResult.findings"
                :key="finding.materialId"
                class="rounded-[10px] border border-sw-line bg-white p-4"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <strong class="text-[#17243a]">{{ finding.code }}</strong>
                  <span class="rounded-full bg-[#fff2f0] px-2 py-1 text-xs font-bold text-sw-danger">{{ finding.severity }}</span>
                  <span class="rounded-full bg-[#f4f8fd] px-2 py-1 text-xs font-bold text-sw-muted">{{ finding.materialDisplayName }}</span>
                </div>
                <p class="mt-2 leading-[1.7] text-[#405574]">{{ finding.message }}</p>
                <p class="mt-1 text-sm leading-[1.7] text-sw-muted">{{ finding.applicantMessage }}</p>
              </article>
            </div>

            <EmptyState v-else title="没有缺失问题" description="当前三类 MVP 材料均已提交，完整性工具未返回问题提示。" />
          </div>

          <EmptyState v-else title="等待完整性检查" description="勾选材料后可演示缺失项、问题提示和完整状态。" />
        </section>
      </section>

      <aside class="sticky top-[88px] grid gap-5 max-xl:static">
        <section class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-card">
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="text-[18px] font-black text-[#17243a]">最近请求 / 响应</h2>
            <span class="rounded-full bg-[#eef6ff] px-2.5 py-1 text-xs font-bold text-sw-primary">{{ lastCallLabel }}</span>
          </div>
          <div class="grid gap-3">
            <div>
              <h3 class="mb-2 text-sm font-black text-[#26364f]">Request JSON</h3>
              <pre class="max-h-[220px] overflow-auto rounded-[10px] bg-[#101827] p-4 text-xs leading-[1.6] text-[#d7e4f7]">{{ requestJson }}</pre>
            </div>
            <div>
              <h3 class="mb-2 text-sm font-black text-[#26364f]">Response JSON</h3>
              <pre class="max-h-[320px] overflow-auto rounded-[10px] bg-[#101827] p-4 text-xs leading-[1.6] text-[#d7e4f7]">{{ responseJson }}</pre>
            </div>
          </div>
        </section>

        <section class="rounded-sw border border-sw-line bg-white p-5 shadow-sw-card">
          <h2 class="mb-4 text-[18px] font-black text-[#17243a]">接口契约样例</h2>
          <div class="grid gap-4">
            <article v-for="example in contractExamples" :key="example.tool" class="border-b border-sw-line pb-4 last:border-b-0 last:pb-0">
              <div class="flex flex-wrap items-center gap-2">
                <strong class="text-[#17243a]">{{ example.tool }}</strong>
                <code>{{ example.endpoint }}</code>
              </div>
              <dl class="mt-3 grid gap-2">
                <div v-for="field in example.fields" :key="`${example.tool}-${field.name}`" class="grid gap-1">
                  <dt class="font-mono text-xs font-bold text-sw-primary">{{ field.name }}</dt>
                  <dd class="m-0 text-sm leading-[1.6] text-sw-muted">{{ field.description }}</dd>
                </div>
              </dl>
            </article>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { callCheckCompleteness, callKnowledgeSearch, getMcpContractExamples, formatToolName } from '@/api/mcpDemo'
import type {
  CheckCompletenessView,
  KnowledgeSearchView,
  MaterialType,
  McpCallSource,
  McpServiceStatusView,
  McpToolName,
} from '@/types'
import { MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'
import EmptyState from '@/components/common/EmptyState.vue'

const searchQuery = ref('取水许可 材料')
const topK = ref(5)
const selectedMaterials = ref<MaterialType[]>(['APPLICATION_FORM', 'BUSINESS_LICENSE'])
const allowDemoFallback = ref(true)

const searchLoading = ref(false)
const completenessLoading = ref(false)
const searchError = ref('')
const completenessError = ref('')
const searchResult = ref<KnowledgeSearchView | null>(null)
const completenessResult = ref<CheckCompletenessView | null>(null)
const lastRequest = ref<unknown | null>(null)
const lastResponse = ref<unknown | null>(null)

const status = reactive<McpServiceStatusView>({
  knowledgePackStatus: 'demo',
  mcpStatus: 'demo',
  knowledgePackVersion: '未调用',
  lastToolName: null,
  lastCalledAt: null,
  lastSource: null,
  lastError: null,
})

const contractExamples = getMcpContractExamples()

const lastCallLabel = computed(() => status.lastToolName ? formatToolName(status.lastToolName) : '等待调用')
const requestJson = computed(() => stringifyJson(lastRequest.value ?? contractExamples[0].request))
const responseJson = computed(() => stringifyJson(lastResponse.value ?? contractExamples[0].response))

async function runSearch() {
  searchError.value = ''
  searchLoading.value = true
  const requestBody = {
    query: searchQuery.value,
    topK: Number.isFinite(topK.value) ? topK.value : 5,
  }
  lastRequest.value = { tool: 'knowledge_search', ...requestBody }

  try {
    const result = await callKnowledgeSearch(requestBody, { allowDemoFallback: allowDemoFallback.value })
    searchResult.value = result
    lastResponse.value = result
    applySuccessfulCall('knowledge_search', result.source, result.requestedAt, result.knowledgePackVersion)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'knowledge_search 调用失败。'
    searchError.value = message
    applyFailedCall('knowledge_search', message)
  } finally {
    searchLoading.value = false
  }
}

async function runCompleteness() {
  completenessError.value = ''
  completenessLoading.value = true
  const requestBody = { materials: selectedMaterials.value }
  lastRequest.value = { tool: 'check_completeness', ...requestBody }

  try {
    const result = await callCheckCompleteness(requestBody, { allowDemoFallback: allowDemoFallback.value })
    completenessResult.value = result
    lastResponse.value = result
    applySuccessfulCall('check_completeness', result.source, result.requestedAt, result.knowledgePackVersion)
  } catch (error) {
    const message = error instanceof Error ? error.message : 'check_completeness 调用失败。'
    completenessError.value = message
    applyFailedCall('check_completeness', message)
  } finally {
    completenessLoading.value = false
  }
}

function applySuccessfulCall(
  toolName: McpToolName,
  source: McpCallSource,
  requestedAt: string,
  knowledgePackVersion: string,
) {
  status.lastToolName = toolName
  status.lastCalledAt = requestedAt
  status.lastSource = source
  status.lastError = source === 'demo' ? 'MCP HTTP 适配服务未返回结果，当前展示本地演示数据。' : null
  status.knowledgePackVersion = knowledgePackVersion
  status.knowledgePackStatus = source === 'live' ? 'available' : 'demo'
  status.mcpStatus = source === 'live' ? 'connected' : 'demo'
}

function applyFailedCall(toolName: McpToolName, message: string) {
  status.lastToolName = toolName
  status.lastCalledAt = new Date().toISOString()
  status.lastSource = null
  status.lastError = message
  status.knowledgePackStatus = 'unavailable'
  status.mcpStatus = 'unavailable'
  lastResponse.value = { error: message }
}

function selectAllMaterials() {
  selectedMaterials.value = [...MATERIAL_SLOTS]
}

function statusLabel(value: McpServiceStatusView['knowledgePackStatus'] | McpServiceStatusView['mcpStatus']) {
  if (value === 'available' || value === 'connected') return '在线'
  if (value === 'demo') return '演示数据'
  return '不可用'
}

function statusDotClass(value: McpServiceStatusView['knowledgePackStatus'] | McpServiceStatusView['mcpStatus']) {
  if (value === 'available' || value === 'connected') return 'bg-sw-success shadow-[0_0_0_5px_rgba(22,178,107,0.12)]'
  if (value === 'demo') return 'bg-sw-warning shadow-[0_0_0_5px_rgba(245,159,0,0.12)]'
  return 'bg-sw-danger shadow-[0_0_0_5px_rgba(240,68,56,0.12)]'
}

function sourceLabel(source: McpCallSource | null) {
  if (source === 'live') return '实时服务'
  if (source === 'demo') return '演示兜底'
  return '未调用'
}

function sourceBadgeClass(source: McpCallSource) {
  return source === 'live' ? 'bg-[#f1fbf6] text-sw-success' : 'bg-[#fff8e8] text-[#9a6700]'
}

function listText(values: string[]) {
  return values.length ? values.join(', ') : '无'
}

function materialListText(values: MaterialType[]) {
  return values.length ? values.map((item) => MATERIAL_LABELS[item]).join('、') : '无'
}

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const pad = (numberValue: number) => String(numberValue).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function stringifyJson(value: unknown): string {
  return JSON.stringify(value, null, 2)
}
</script>
