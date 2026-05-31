<template>
  <div class="sw-page max-w-[1480px]">
    <div class="flex items-start justify-between gap-5 max-md:block">
      <div>
        <h1 class="sw-page-title">AI 知识库与 MCP 演示台</h1>
        <p class="mb-[22px] mt-[-12px] leading-[1.7] text-sw-muted">
          真实请求 Java 后端完成 MCP 测活、入库演示和工具调用；页面结果仅作辅助演示，非正式审批结论。
        </p>
      </div>
      <div class="flex flex-wrap justify-end gap-3 max-md:mt-3">
        <button type="button" class="sw-btn sw-btn-primary" :disabled="statusLoading" @click="loadStatus">
          {{ statusLoading ? '检查中...' : '检查 MCP 健康' }}
        </button>
        <button type="button" class="sw-btn sw-btn-ghost" :disabled="ingestLoading" @click="loadIngestOperation">
          {{ ingestLoading ? '刷新中...' : '刷新入库演示' }}
        </button>
      </div>
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

    <div v-if="statusError" class="sw-alert sw-alert-danger mb-4">
      {{ statusError }}
      <button type="button" class="ml-3 font-bold text-sw-danger underline" @click="loadStatus">重试测活</button>
    </div>

    <PageCard title="MCP 健康检查" subtitle="通过 Java /api/ai/health 真实请求 Python FastAPI 与 MCP 配置。" compact class="mb-5">
      <div v-if="health" class="grid gap-3 [grid-template-columns:repeat(3,minmax(0,1fr))] max-[1180px]:grid-cols-1">
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">AI 服务地址</p>
          <code class="mt-2 block [overflow-wrap:anywhere] text-[#12213a]">{{ health.baseUrl }}</code>
        </div>
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">健康检查地址</p>
          <code class="mt-2 block [overflow-wrap:anywhere] text-[#12213a]">{{ health.healthUrl }}</code>
        </div>
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">MCP 地址</p>
          <code class="mt-2 block [overflow-wrap:anywhere] text-[#12213a]">{{ health.mcpUrl || '未配置' }}</code>
        </div>
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">Transport</p>
          <strong class="mt-2 block text-[#12213a]">{{ health.mcpTransport || '未配置' }}</strong>
        </div>
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">HTTP 状态</p>
          <strong class="mt-2 block text-[#12213a]">{{ health.statusCode ?? '无响应' }}</strong>
        </div>
        <div class="rounded-[10px] bg-[#f6f9fd] p-4">
          <p class="text-xs font-bold text-sw-muted">检查时间</p>
          <strong class="mt-2 block text-[#12213a]">{{ formatDateTime(health.checkedAt) }}</strong>
        </div>
      </div>
      <div v-else class="sw-alert sw-alert-info">
        点击“检查 MCP 健康”后，这里会展示 Java 后端返回的真实健康检查结果。
      </div>
      <pre v-if="health?.responseBody" class="mt-4 overflow-auto rounded-[10px] bg-[#111827] p-4 text-xs leading-[1.7] text-[#dbeafe]">{{ health.responseBody }}</pre>
    </PageCard>

    <div class="grid items-start gap-5 [grid-template-columns:minmax(420px,1fr)_minmax(420px,1fr)] max-[1180px]:grid-cols-1">
      <PageCard title="knowledge_search" subtitle="输入查询词，展示知识库命中结果和依据片段。" compact>
        <div class="grid gap-3 [grid-template-columns:minmax(0,1fr)_120px_auto] max-md:grid-cols-1">
          <input v-model="searchQuery" class="sw-input" placeholder="例如：取水许可 材料" @keyup.enter="runKnowledgeSearch" />
          <input v-model.number="searchTopK" class="sw-input" type="number" min="1" max="50" />
          <button type="button" class="sw-btn sw-btn-primary" :disabled="searchLoading" @click="runKnowledgeSearch">
            {{ searchLoading ? '检索中...' : '检索' }}
          </button>
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
            :key="`${item.section}-${item.id}`"
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
          <button type="button" class="sw-btn sw-btn-primary" :disabled="completenessLoading" @click="runCompletenessCheck">
            {{ completenessLoading ? '检查中...' : '检查完整性' }}
          </button>
        </div>

        <div v-if="completenessError" class="sw-alert sw-alert-danger mt-4">
          {{ completenessError }}
          <button type="button" class="ml-3 font-bold text-sw-danger underline" @click="runCompletenessCheck">重试</button>
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

    <PageCard title="文档解析入库演示" subtitle="通过 Java /api/ai/ingest 获取可复现的 Python ingest 命令，不在页面里伪造远程执行。" compact class="mt-5">
      <div v-if="ingestError" class="sw-alert sw-alert-danger mb-4">
        {{ ingestError }}
        <button type="button" class="ml-3 font-bold text-sw-danger underline" @click="loadIngestOperation">重试</button>
      </div>

      <div v-if="ingestOperation" class="grid gap-4">
        <div class="grid gap-3 [grid-template-columns:repeat(4,minmax(0,1fr))] max-[1180px]:grid-cols-2 max-md:grid-cols-1">
          <div class="rounded-[10px] bg-[#f6f9fd] p-4">
            <p class="text-xs font-bold text-sw-muted">模式</p>
            <strong class="mt-2 block text-[#12213a]">{{ ingestOperation.mode }}</strong>
          </div>
          <div class="rounded-[10px] bg-[#f6f9fd] p-4">
            <p class="text-xs font-bold text-sw-muted">Chunk</p>
            <strong class="mt-2 block text-[#12213a]">{{ ingestOperation.chunkSize }} / {{ ingestOperation.chunkOverlap }}</strong>
          </div>
          <div class="rounded-[10px] bg-[#f6f9fd] p-4">
            <p class="text-xs font-bold text-sw-muted">重建</p>
            <strong class="mt-2 block text-[#12213a]">{{ ingestOperation.rebuild ? '是' : '否' }}</strong>
          </div>
          <div class="rounded-[10px] bg-[#f6f9fd] p-4">
            <p class="text-xs font-bold text-sw-muted">演示来源</p>
            <strong class="mt-2 block text-[#12213a]">真实 Java 接口</strong>
          </div>
        </div>

        <div class="grid gap-4 [grid-template-columns:repeat(2,minmax(0,1fr))] max-[1180px]:grid-cols-1">
          <div class="min-w-0 rounded-[10px] border border-sw-line bg-white p-4">
            <p class="text-xs font-bold text-sw-muted">工作目录</p>
            <code class="mt-2 block [overflow-wrap:anywhere] text-[#12213a]">{{ ingestOperation.workdir }}</code>
          </div>
          <div class="min-w-0 rounded-[10px] border border-sw-line bg-white p-4">
            <p class="text-xs font-bold text-sw-muted">资料目录</p>
            <code class="mt-2 block [overflow-wrap:anywhere] text-[#12213a]">{{ ingestOperation.sourceDir }}</code>
          </div>
        </div>

        <div class="min-w-0">
          <h3 class="mb-3 text-base font-black text-[#16233b]">解析入库命令</h3>
          <pre class="overflow-auto rounded-[10px] bg-[#111827] p-4 text-xs leading-[1.7] text-[#dbeafe]">{{ formatCommand(ingestOperation.command) }}</pre>
        </div>
        <div class="min-w-0">
          <h3 class="mb-3 text-base font-black text-[#16233b]">MCP 工具验证命令</h3>
          <pre class="overflow-auto rounded-[10px] bg-[#111827] p-4 text-xs leading-[1.7] text-[#dbeafe]">{{ ingestOperation.verificationCommand }}</pre>
        </div>
        <div class="sw-alert sw-alert-info">{{ ingestOperation.note }}</div>
      </div>

      <div v-else class="sw-alert sw-alert-info">
        点击“刷新入库演示”后，这里会展示后端返回的文档解析、chunk、向量入库和 MCP 验证命令。
      </div>
    </PageCard>

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
import {
  buildDemoCompleteness,
  buildDemoKnowledgeSearch,
  buildDemoStatus,
  callCheckCompletenessTool,
  callKnowledgeSearchTool,
  getAiHealth,
  getAiIngestOperation,
  toKnowledgeStatusFromAiHealth,
} from '@/api/knowledge'
import type {
  AiHealthResponse,
  AiIngestOperationResponse,
  CompletenessResponse,
  KnowledgeSearchResponse,
  KnowledgeStatusView,
  MaterialType,
  McpToolName,
} from '@/types'
import { MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const status = ref<KnowledgeStatusView>(buildDemoStatus())
const statusLoading = ref(false)
const statusError = ref('')
const health = ref<AiHealthResponse | null>(null)
const ingestOperation = ref<AiIngestOperationResponse | null>(null)
const ingestLoading = ref(false)
const ingestError = ref('')

const searchQuery = ref('取水许可 材料')
const searchTopK = ref(5)
const searchLoading = ref(false)
const searchError = ref('')
const searchResult = ref<KnowledgeSearchResponse | null>(null)

const selectedMaterials = ref<MaterialType[]>(['APPLICATION_FORM', 'BUSINESS_LICENSE'])
const completenessLoading = ref(false)
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
  loadStatus()
  loadIngestOperation()
  runKnowledgeSearch()
  runCompletenessCheck()
})

async function loadStatus() {
  statusLoading.value = true
  statusError.value = ''
  try {
    const response = await getAiHealth()
    health.value = response
    status.value = toKnowledgeStatusFromAiHealth(response, status.value.lastToolName)
  } catch (error) {
    statusError.value = error instanceof Error ? error.message : 'MCP 健康检查失败，请重试。'
    status.value = buildDemoStatus(status.value.lastToolName, '真实健康检查失败；工具按钮仍会走 Java 后端 MCP 代理。')
  } finally {
    statusLoading.value = false
  }
}

async function loadIngestOperation() {
  ingestLoading.value = true
  ingestError.value = ''
  try {
    ingestOperation.value = await getAiIngestOperation()
  } catch (error) {
    ingestError.value = error instanceof Error ? error.message : '文档解析入库演示信息加载失败，请重试。'
  } finally {
    ingestLoading.value = false
  }
}

async function runKnowledgeSearch() {
  searchLoading.value = true
  searchError.value = ''
  searchResult.value = null
  try {
    const params = buildKnowledgeSearchParams()
    searchResult.value = await callKnowledgeSearchTool(params)
    markToolCall('knowledge_search', '已通过 Java 后端调用 Python MCP knowledge_search。', 'api')
  } catch (error) {
    searchError.value = error instanceof Error ? error.message : 'knowledge_search 调用失败，请重试。'
  } finally {
    searchLoading.value = false
  }
}

async function runCompletenessCheck() {
  completenessLoading.value = true
  completenessError.value = ''
  completenessResult.value = null
  try {
    completenessResult.value = await callCheckCompletenessTool(selectedMaterials.value)
    markToolCall('check_completeness', '已通过 Java 后端调用 Python MCP check_completeness。', 'api')
  } catch (error) {
    completenessError.value = error instanceof Error ? error.message : 'check_completeness 调用失败，请重试。'
  } finally {
    completenessLoading.value = false
  }
}

function runEmptyKnowledgeSearch() {
  searchQuery.value = '无匹配演示查询'
  runKnowledgeSearch()
}

function runFailedKnowledgeSearch() {
  searchLoading.value = true
  searchError.value = ''
  searchResult.value = null
  window.setTimeout(() => {
    searchResult.value = buildDemoKnowledgeSearch({ query: 'simulate-error', topK: 1 })
    searchError.value = '本地失败演示：真实 knowledge_search 请使用“检索”按钮。'
    searchLoading.value = false
  }, 250)
}

function runEmptyCompletenessCheck() {
  selectedMaterials.value = [...MATERIAL_SLOTS]
  runCompletenessCheck()
}

function runFailedCompletenessCheck() {
  completenessLoading.value = true
  completenessError.value = ''
  completenessResult.value = null
  window.setTimeout(() => {
    completenessResult.value = buildDemoCompleteness([])
    completenessError.value = '本地失败演示：真实 check_completeness 请使用“检查完整性”按钮。'
    completenessLoading.value = false
  }, 250)
}

function buildKnowledgeSearchParams() {
  if (!Number.isFinite(searchTopK.value) || searchTopK.value < 1 || searchTopK.value > 50) {
    throw new Error('topK 需要在 1-50 之间，请修改后重试。')
  }
  return { query: searchQuery.value, topK: searchTopK.value }
}

function markToolCall(toolName: McpToolName, message: string, source: 'api' | 'demo') {
  status.value = {
    ...status.value,
    lastToolName: toolName,
    lastCalledAt: new Date().toISOString(),
    source: health.value ? 'api' : source,
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

function formatCommand(command: string[]): string {
  return command.map((part) => {
    if (/^[A-Za-z0-9_./:=@-]+$/.test(part)) {
      return part
    }
    return `'${part.replaceAll("'", "'\\''")}'`
  }).join(' ')
}
</script>
