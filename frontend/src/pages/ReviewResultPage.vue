<template>
  <div class="sw-page max-w-[1480px]">
    <div class="flex items-start justify-between gap-5 max-md:block">
      <div>
        <h1 class="sw-page-title">AI 智能审核结果</h1>
        <p class="mb-[22px] mt-[-12px] leading-[1.7] text-sw-muted">
          AI 结果用于审批辅助建议，不构成正式审批决定。最终结论以审批人员处理结果为准。
        </p>
      </div>
      <router-link class="sw-btn sw-btn-ghost" to="/">返回申请列表</router-link>
    </div>

    <PageCard v-if="!task" title="查询任务" subtitle="请输入任务 ID。系统会按登录角色进行后端权限校验。" compact>
      <div class="grid gap-3 [grid-template-columns:minmax(220px,1fr)_auto] max-md:grid-cols-1">
        <input v-model="inputTaskId" class="sw-input" placeholder="任务 ID" @keyup.enter="lookup" />
        <button type="button" class="sw-btn sw-btn-primary" :disabled="loading" @click="lookup">
          {{ loading ? '查询中...' : '查询' }}
        </button>
      </div>
      <p v-if="lookupError" class="mt-3 text-sw-danger">{{ lookupError }}</p>
    </PageCard>

    <div v-if="loading && !task" class="sw-alert sw-alert-info mt-[14px] flex items-center gap-2.5">
      <span class="sw-spinner"></span>
      <span>正在读取任务状态和 AI 初审结果</span>
    </div>

    <div v-if="task" class="grid items-start gap-6 [grid-template-columns:minmax(420px,1.25fr)_minmax(430px,0.95fr)] max-[1180px]:grid-cols-1">
      <section class="grid gap-4">
        <PageCard compact class="overflow-hidden !p-0">
          <div class="grid min-h-14 items-center bg-gradient-to-b from-[#1f2933] to-[#111827] px-5 text-white [grid-template-columns:1fr_auto_1fr] max-md:grid-cols-1 max-md:gap-1 max-md:px-4 max-md:py-3 max-md:text-center">
            <span></span>
            <strong>材料与任务信息</strong>
            <small class="justify-self-end text-[#cbd5e1] max-md:justify-self-center">{{ uploadedCount }}/{{ task.materials.length }} 已提交</small>
          </div>

          <div class="grid gap-4 bg-[linear-gradient(90deg,rgba(15,23,42,0.035)_1px,transparent_1px),linear-gradient(rgba(15,23,42,0.035)_1px,transparent_1px),#fbfcff] bg-[length:24px_24px] px-5 py-5 max-md:px-4">
            <article
              v-for="slot in task.previewMaterials"
              :key="slot.materialType"
              class="overflow-hidden rounded-[16px] border border-sw-line bg-white shadow-[0_8px_24px_rgba(15,23,42,0.05)]"
            >
              <div class="flex items-center justify-between gap-3 border-b border-sw-line px-4 py-3 max-md:block">
                <div>
                  <strong class="text-[#172033]">{{ MATERIAL_LABELS[slot.materialType] }}</strong>
                  <p class="mt-1 text-sm text-sw-muted">{{ slot.originalFileName || '未上传材料' }}</p>
                </div>
                <span
                  class="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-bold"
                  :class="slot.uploaded ? 'border-sw-primary bg-[#f1f7ff] text-sw-primary' : 'border-[#ffe1a6] bg-[#fff8e8] text-[#9a6700]'"
                >
                  {{ slot.uploaded ? '可检查' : '缺失' }}
                </span>
              </div>

              <div class="grid min-h-[260px] place-items-center bg-[#f8fafc] p-4">
                <template v-if="slot.kind === 'missing'">
                  <PreviewMessage
                    title="材料未上传"
                    description="当前槽位没有原始材料，无法提供预览。"
                  />
                </template>

                <template v-else-if="slot.kind === 'unsupported'">
                  <PreviewMessage
                    title="暂不支持预览"
                    description="当前文件格式不在前端预览范围内，请联系后端确认接口返回的文件类型。"
                  />
                </template>

                <template v-else-if="previewState(slot.materialType).status === 'loading'">
                  <div class="flex items-center gap-2 text-sw-muted">
                    <span class="sw-spinner"></span>
                    <span>正在加载材料预览</span>
                  </div>
                </template>

                <template v-else-if="isPreviewMessageState(previewState(slot.materialType).status)">
                  <PreviewMessage
                    title="预览加载失败"
                    :description="previewState(slot.materialType).message || '后端未返回可用的预览内容。'"
                  />
                </template>

                <template v-else-if="slot.kind === 'pdf' && previewState(slot.materialType).objectUrl">
                  <iframe
                    :src="previewState(slot.materialType).objectUrl!"
                    class="h-[420px] w-full rounded-[12px] border border-sw-line bg-white"
                    title="PDF 材料预览"
                  />
                </template>

                <template v-else-if="slot.kind === 'image' && previewState(slot.materialType).objectUrl">
                  <img
                    :src="previewState(slot.materialType).objectUrl!"
                    :alt="slot.originalFileName || MATERIAL_LABELS[slot.materialType]"
                    class="max-h-[420px] w-auto max-w-full rounded-[12px] border border-sw-line bg-white object-contain"
                  />
                </template>

                <template v-else>
                  <PreviewMessage
                    title="暂无预览内容"
                    description="前端正在等待预览地址或二进制内容返回。"
                  />
                </template>
              </div>
            </article>
          </div>

          <div class="flex gap-3 border-t border-sw-line bg-white px-5 py-4">
            <div
              v-for="slot in task.materials"
              :key="slot.materialType"
              class="grid h-[54px] w-[70px] place-items-center rounded-lg border text-xs font-extrabold"
              :class="slot.uploaded ? 'border-sw-primary bg-[#f1f7ff] text-sw-primary' : 'border-[#ffe1a6] bg-[#fff8e8] text-[#9a6700]'"
            >
              <span>{{ materialShortName(slot.materialType) }}</span>
            </div>
          </div>
        </PageCard>

        <PageCard title="任务信息" compact>
          <dl class="m-0 grid [grid-template-columns:86px_1fr] gap-x-4 gap-y-[13px]">
            <dt class="font-bold text-sw-muted">任务状态</dt>
            <dd class="m-0 min-w-0"><StatusTag :status="task.status" /></dd>
            <template v-if="task.handlingStatusLabel">
              <dt class="font-bold text-sw-muted">处理结果</dt>
              <dd class="m-0 min-w-0">
                <span class="inline-flex items-center rounded-full border border-sw-line-strong bg-[#f6f9fd] px-2.5 py-1 text-xs font-bold text-[#2b4362]">
                  {{ task.handlingStatusLabel }}
                </span>
              </dd>
            </template>
            <dt class="font-bold text-sw-muted">任务 ID</dt>
            <dd class="m-0 min-w-0"><code>{{ inputTaskId }}</code></dd>
            <dt class="font-bold text-sw-muted">材料提交情况</dt>
            <dd class="m-0 min-w-0"><TaskMaterialSummary :slots="task.materials" variant="stacked" /></dd>
            <template v-if="task.reviewerRemark">
              <dt class="font-bold text-sw-muted">审批备注</dt>
              <dd class="m-0 min-w-0 leading-[1.7] text-[#2b4362]">{{ task.reviewerRemark }}</dd>
            </template>
          </dl>
        </PageCard>
      </section>

      <section class="grid gap-4">
        <PageCard compact class="overflow-hidden">
          <div class="mb-[18px] mt-[-2px] flex justify-between gap-5 border-b border-sw-line pb-[18px] max-md:block">
            <div>
              <h2 class="text-[19px] font-black text-[#12213a]">AI 分析面板</h2>
              <p class="mt-2 leading-[1.7] text-sw-muted">{{ summaryText }}</p>
            </div>
            <div class="grid h-[78px] w-[78px] flex-none place-items-center rounded-full bg-[radial-gradient(circle_at_35%_30%,#ffffff,transparent_34%),linear-gradient(135deg,#51b3ff,#1677ff_64%,#7ad6ff)] text-[25px] font-black text-white shadow-[0_0_0_8px_rgba(22,119,255,0.08),0_12px_30px_rgba(22,119,255,0.25)] max-md:mt-[14px]">
              AI
            </div>
          </div>

          <StatusBanner
            :status="task.status"
            :resultSummary="task.summary"
            :requiresManualReview="task.requiresManualReview"
            :audience="task.viewMode"
          />

          <div v-if="task.requiresManualReview" class="sw-alert sw-alert-warning mb-4">
            {{ task.manualReviewNotice || '审核结果中存在阻断性问题或模型/系统异常，请人工复核后继续办理。' }}
          </div>

          <FailureInfo
            v-if="task.status === 'FAILED' || task.failureCategory"
            :failureCategory="task.failureCategory"
            :failureReason="task.failureReason"
          />

          <div v-if="task.viewMode === 'REVIEWER' && Object.keys(task.extractedFields).length" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">抽取字段</h3>
            <div class="grid gap-3 [grid-template-columns:repeat(2,minmax(0,1fr))] max-md:grid-cols-1">
              <div v-for="(value, key) in task.extractedFields" :key="key" class="grid gap-1.5 rounded-[10px] bg-[#f6f9fd] p-3">
                <span class="text-xs text-sw-muted">{{ key }}</span>
                <strong class="min-w-0 [overflow-wrap:anywhere] text-[#20304a]">{{ value || '未返回' }}</strong>
              </div>
            </div>
          </div>

          <div class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">合规检查清单</h3>
            <div v-if="task.findings.length" class="grid gap-2.5">
              <article
                v-for="finding in task.findings"
                :key="`${finding.findingType}-${finding.description}`"
                class="grid gap-2.5 border-b border-[#edf2f7] py-2.5 [grid-template-columns:24px_1fr]"
              >
                <span
                  class="grid h-[22px] w-[22px] place-items-center rounded-full text-xs font-black text-white"
                  :class="severityDotClass(finding.severity)"
                >
                  {{ severityIcon(finding.severity) }}
                </span>
                <div>
                  <strong class="text-[#23405e]">{{ finding.findingType }}</strong>
                  <p class="mt-1 leading-[1.65] text-[#34516f]">{{ finding.description }}</p>
                  <small v-if="finding.basis" class="mt-[5px] inline-block text-sw-muted">依据：{{ finding.basis }}</small>
                </div>
              </article>
            </div>
            <EmptyState v-else title="暂无问题清单" description="后端未返回问题项，仍需以人工审批结论为准。" />
          </div>

          <div v-if="task.viewMode === 'REVIEWER' && task.riskHints.length" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">风险提示</h3>
            <ul class="m-0 grid list-none gap-2.5 p-0">
              <li v-for="hint in task.riskHints" :key="hint" class="rounded-lg border-l-4 border-sw-warning bg-[#fff8e8] px-3 py-2.5 leading-[1.7] text-[#714b00]">
                {{ hint }}
              </li>
            </ul>
          </div>

          <div v-if="task.viewMode === 'REVIEWER' && task.draftOpinion" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">审核意见草稿</h3>
            <p class="whitespace-pre-wrap rounded-[10px] bg-[#f6f9fd] p-[14px] leading-[1.8] text-slate-700">{{ task.draftOpinion }}</p>
            <small class="mt-2 inline-block text-sw-warning">草稿仅供审批人员参考，不构成最终审批决定。</small>
          </div>

          <div v-if="canShowReviewerActionPanel" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">审核处理</h3>
            <p class="mb-3 leading-[1.7] text-sw-muted">请选择处理动作并填写备注（可选）。若任务已处理，将显示历史处理结果并禁用重复提交。</p>

            <div v-if="actionErrorMessage" class="sw-alert sw-alert-danger mb-3">
              {{ actionErrorMessage }}
            </div>
            <div v-if="actionSuccessMessage" class="sw-alert sw-alert-info mb-3">
              {{ actionSuccessMessage }}
            </div>
            <div v-if="reviewerActionCompleted" class="sw-alert sw-alert-warning mb-3">
              当前任务已完成处理：{{ task.handlingStatusLabel || '已处理' }}，不可重复提交。
            </div>

            <label class="mb-3 grid gap-2">
              <span class="font-extrabold text-[#26364f]">处理备注（选填）</span>
              <textarea
                v-model="reviewerRemarkInput"
                class="sw-input min-h-[98px] py-2"
                placeholder="例如：请补充缺失材料并重新提交。"
                :disabled="reviewerActionSubmitting || reviewerActionCompleted"
                maxlength="1000"
              />
            </label>

            <div class="grid gap-3 [grid-template-columns:repeat(3,minmax(0,1fr))] max-md:grid-cols-1">
              <button
                type="button"
                class="sw-btn sw-btn-primary"
                :disabled="reviewerActionSubmitting || reviewerActionCompleted || !reviewerActionAllowed"
                @click="submitAction('APPROVE_INITIAL_REVIEW')"
              >
                {{ reviewerActionSubmitting ? '提交中...' : '通过初审' }}
              </button>
              <button
                type="button"
                class="sw-btn sw-btn-ghost"
                :disabled="reviewerActionSubmitting || reviewerActionCompleted || !reviewerActionAllowed"
                @click="submitAction('RETURN_FOR_CORRECTION')"
              >
                退回补正
              </button>
              <button
                type="button"
                class="sw-btn sw-btn-ghost"
                :disabled="reviewerActionSubmitting || reviewerActionCompleted || !reviewerActionAllowed"
                @click="submitAction('TRANSFER_MANUAL_REVIEW')"
              >
                转人工复核
              </button>
            </div>
            <p v-if="!reviewerActionAllowed" class="mt-2 text-xs text-sw-muted">
              当前任务状态为 {{ task.status }}，仅 `PARTIAL_SUCCESS` 或 `COMPLETED` 允许提交处理动作。
            </p>
          </div>

          <div v-if="task.viewMode === 'REVIEWER'" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">处理日志</h3>
            <ul v-if="task.reviewActionLogs.length" class="m-0 grid list-none gap-2.5 p-0">
              <li
                v-for="log in task.reviewActionLogs"
                :key="`${log.actionCode}-${log.operatedAt || 'na'}-${log.operatorUserId || 'na'}`"
                class="rounded-[10px] border border-sw-line bg-[#f8fbff] p-3 leading-[1.7] text-[#2b4362]"
              >
                <div class="flex items-center justify-between gap-3 max-md:block">
                  <strong>{{ log.actionLabel || log.actionCode }}</strong>
                  <span class="text-xs text-sw-muted">{{ formatDateTime(log.operatedAt) }}</span>
                </div>
                <div class="mt-1 text-sm text-sw-muted">
                  操作人：{{ log.operatorDisplayName || `用户#${log.operatorUserId ?? '未知'}` }}
                </div>
                <div v-if="log.reviewerRemark" class="mt-1">备注：{{ log.reviewerRemark }}</div>
              </li>
            </ul>
            <EmptyState v-else title="暂无处理日志" description="当前任务尚未提交审核动作。" />
          </div>
        </PageCard>

        <div class="grid gap-4 [grid-template-columns:repeat(2,minmax(0,1fr))] max-md:grid-cols-1">
          <router-link v-if="isApplicantView" class="sw-btn sw-btn-ghost" to="/apply">返回申请</router-link>
          <router-link v-else class="sw-btn sw-btn-ghost" to="/">返回待办</router-link>
          <button type="button" class="sw-btn sw-btn-ghost" @click="lookup" :disabled="loading">
            {{ loading ? '刷新中...' : '重新查询' }}
          </button>
        </div>
      </section>
    </div>

    <p class="mt-5 text-center text-xs leading-[1.7] text-sw-faint">本系统提供 AI 辅助审核建议，最终审核结果以审批机关决定为准。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  fetchMaterialPreviewBlob,
  getMaterialPreviewErrorState,
  getApplicantResult,
  getReviewerResult,
  getTaskStatus,
  submitReviewerAction,
  toApplicantTaskResultView,
  toApplicantResultView,
  toReviewerResultView,
  isReviewerActionCompleted,
} from '@/api/task'
import { getCurrentRole } from '@/utils/auth'
import type {
  MaterialPreviewItem,
  MaterialPreviewLoadStatus,
  MaterialType,
  ReviewerActionCode,
  Severity,
  TaskResultView,
} from '@/types'
import { MATERIAL_LABELS } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import StatusBanner from '@/components/business/StatusBanner.vue'
import FailureInfo from '@/components/business/FailureInfo.vue'
import TaskMaterialSummary from '@/components/business/TaskMaterialSummary.vue'

const PreviewMessage = defineComponent({
  name: 'PreviewMessage',
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'grid place-items-center gap-3 text-center' }, [
      h('div', { class: 'grid h-[92px] w-[92px] place-items-center rounded-[24px] bg-[#eef6ff] text-[#6da9f5]' }, 'PDF'),
      h('strong', { class: 'text-lg text-[#172033]' }, props.title),
      h('p', { class: 'max-w-[420px] leading-[1.8] text-sw-muted' }, props.description),
    ])
  },
})

type PreviewLoadState = {
  status: MaterialPreviewLoadStatus
  objectUrl: string | null
  message: string
}

const route = useRoute()

const inputTaskId = ref((route.query.taskId as string) || '')
const task = ref<TaskResultView | null>(null)
const loading = ref(false)
const lookupError = ref('')
const reviewerRemarkInput = ref('')
const reviewerActionSubmitting = ref(false)
const actionErrorMessage = ref('')
const actionSuccessMessage = ref('')
const previewStates = ref<Record<string, PreviewLoadState>>({})
let lookupSequence = 0
let previewLoadSequence = 0

const uploadedCount = computed(() => task.value?.materials.filter((slot) => slot.uploaded).length ?? 0)
const isApplicantView = computed(() => task.value?.viewMode === 'APPLICANT')
const canShowReviewerActionPanel = computed(() => task.value?.viewMode === 'REVIEWER')
const reviewerActionCompleted = computed(() => task.value ? isReviewerActionCompleted(task.value.handlingStatus) : false)
const reviewerActionAllowed = computed(() =>
  task.value?.status === 'PARTIAL_SUCCESS' || task.value?.status === 'COMPLETED',
)

const summaryText = computed(() => {
  if (!task.value) return ''
  if (task.value.failureCategory || task.value.status === 'FAILED') return '处理失败或模型结果异常，需要人工复核。'
  if (task.value.requiresManualReview) return '结果已生成，但存在阻断项或人工复核提示。'
  if (task.value.status === 'PARTIAL_SUCCESS') return '已生成部分结果，请结合缺失材料和风险提示判断。'
  if (task.value.status === 'COMPLETED') return '后端已返回审核辅助结果，可查看字段、问题和草稿意见。'
  return '任务尚未完成，请稍后重新查询。'
})

async function lookup() {
  if (!inputTaskId.value.trim()) {
    lookupError.value = '请输入任务 ID。'
    return
  }

  const currentLookup = ++lookupSequence
  lookupError.value = ''
  loading.value = true
  try {
    const taskId = inputTaskId.value.trim()
    const statusRes = await getTaskStatus(taskId)
    if (currentLookup !== lookupSequence) return
    if (getCurrentRole() === 'APPLICANT') {
      const resultRes = await getApplicantResult(taskId)
      if (currentLookup !== lookupSequence) return
      task.value = toApplicantTaskResultView(
        statusRes.data.data,
        toApplicantResultView(resultRes.data.data),
      )
    } else {
      const resultRes = await getReviewerResult(taskId)
      if (currentLookup !== lookupSequence) return
      task.value = {
        viewMode: 'REVIEWER',
        ...toReviewerResultView(statusRes.data.data, resultRes.data.data),
      }
    }
    actionErrorMessage.value = ''
    actionSuccessMessage.value = ''
    reviewerRemarkInput.value = task.value?.reviewerRemark ?? ''
    resetPreviewStates()
    await loadPreviewAssets(task.value?.previewMaterials ?? [])
  } catch (error) {
    lookupError.value = error instanceof Error ? error.message : '查询失败，请确认任务 ID。'
    task.value = null
    resetPreviewStates()
  } finally {
    loading.value = false
  }
}

async function loadPreviewAssets(items: MaterialPreviewItem[]) {
  const currentLoad = ++previewLoadSequence
  await Promise.all(items.map(async (item) => {
    if (!item.previewPath || item.kind === 'missing' || item.kind === 'unsupported') {
      if (currentLoad !== previewLoadSequence) return
      previewStates.value[item.materialType] = {
        status: 'idle',
        objectUrl: null,
        message: '',
      }
      return
    }

    previewStates.value[item.materialType] = {
      status: 'loading',
      objectUrl: null,
      message: '',
    }

    try {
      const blob = await fetchMaterialPreviewBlob(item.previewPath)
      const objectUrl = URL.createObjectURL(blob)
      if (currentLoad !== previewLoadSequence) {
        URL.revokeObjectURL(objectUrl)
        return
      }
      previewStates.value[item.materialType] = {
        status: 'ready',
        objectUrl,
        message: '',
      }
    } catch (error) {
      if (currentLoad !== previewLoadSequence) return
      const errorState = getMaterialPreviewErrorState(error)
      previewStates.value[item.materialType] = {
        status: errorState.status,
        objectUrl: null,
        message: errorState.message,
      }
    }
  }))
}

function resetPreviewStates() {
  previewLoadSequence += 1
  Object.values(previewStates.value).forEach((state) => {
    if (state.objectUrl) {
      URL.revokeObjectURL(state.objectUrl)
    }
  })
  previewStates.value = {}
}

async function submitAction(actionCode: ReviewerActionCode) {
  if (!task.value || task.value.viewMode !== 'REVIEWER') return
  if (reviewerActionCompleted.value) return
  if (!reviewerActionAllowed.value) return

  reviewerActionSubmitting.value = true
  actionErrorMessage.value = ''
  actionSuccessMessage.value = ''
  try {
    const payload = {
      actionCode,
      reviewerRemark: reviewerRemarkInput.value.trim(),
    }
    const res = await submitReviewerAction(inputTaskId.value.trim(), payload)
    await lookup()
    actionSuccessMessage.value = `处理动作已提交：${res.data.data.handlingStatusLabel || res.data.data.actionLabel || actionCode}`
  } catch (error) {
    const message = error instanceof Error ? error.message : '处理动作提交失败，请稍后重试。'
    actionErrorMessage.value = message
    if (message.includes('已提交过审核动作') || message.includes('状态已变化')) {
      await lookup()
      actionErrorMessage.value = message
    }
  } finally {
    reviewerActionSubmitting.value = false
  }
}

function previewState(materialType: MaterialType): PreviewLoadState {
  return previewStates.value[materialType] ?? {
    status: 'idle',
    objectUrl: null,
    message: '',
  }
}

function isPreviewMessageState(status: MaterialPreviewLoadStatus): boolean {
  return status === 'forbidden'
    || status === 'not_found'
    || status === 'unsupported'
    || status === 'error'
}

function materialShortName(type: MaterialType): string {
  return MATERIAL_LABELS[type].slice(0, 2)
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return '未返回'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function severityDotClass(severity: Severity): string {
  if (severity === 'BLOCKER') return 'bg-sw-danger'
  if (severity === 'WARNING') return 'bg-sw-warning'
  return 'bg-sw-info'
}

function severityIcon(severity: Severity): string {
  if (severity === 'BLOCKER') return '!'
  if (severity === 'WARNING') return '•'
  return 'i'
}

onBeforeUnmount(() => {
  resetPreviewStates()
})

if (inputTaskId.value) {
  lookup()
}
</script>
