<template>
  <div class="sw-page max-w-[1480px]">
    <div class="flex items-start justify-between gap-5 max-md:block">
      <div>
        <h1 class="sw-page-title">AI 智能审核结果</h1>
        <p class="mb-[22px] mt-[-12px] leading-[1.7] text-sw-muted">AI 结果用于审批辅助；存在失败、阻断项或人工复核提示时，不视为完整通过。</p>
      </div>
      <router-link class="sw-btn sw-btn-ghost" to="/">返回申请列表</router-link>
    </div>

    <PageCard v-if="!task" title="查询任务" subtitle="请输入任务 ID 和会话 ID。MVP 无账号体系，因此不能声明已按用户权限隔离。" compact>
      <div class="grid gap-3 [grid-template-columns:minmax(220px,1fr)_minmax(220px,1fr)_auto] max-md:grid-cols-1">
        <input v-model="inputTaskId" class="sw-input" placeholder="任务 ID" @keyup.enter="lookup" />
        <input v-model="inputSessionId" class="sw-input" placeholder="会话 ID" @keyup.enter="lookup" />
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
          <div class="grid min-h-[455px] place-items-center content-center gap-[14px] bg-[linear-gradient(90deg,rgba(15,23,42,0.035)_1px,transparent_1px),linear-gradient(rgba(15,23,42,0.035)_1px,transparent_1px),#fbfcff] bg-[length:24px_24px] px-11 py-11 text-center max-md:min-h-[300px] max-md:px-[18px] max-md:py-7">
            <div class="grid h-[116px] w-[116px] place-items-center rounded-[28px] bg-[#eef6ff] text-[#6da9f5]" aria-hidden="true">
              <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <path d="M14 2v6h6"/>
                <path d="M8 13h8"/>
                <path d="M8 17h5"/>
              </svg>
            </div>
            <h2 class="text-xl text-[#172033]">不提供伪造证照预览</h2>
            <p class="max-w-[440px] leading-[1.8] text-sw-muted">当前后端返回材料元数据与抽取结果，未返回可安全嵌入的 PDF/图片预览地址。</p>
          </div>
          <div class="flex gap-3 border-t border-sw-line bg-white px-5 py-4">
            <div
              v-for="slot in task.materials"
              :key="slot.materialType"
              class="grid h-[54px] w-[70px] place-items-center rounded-lg border text-xs font-extrabold"
              :class="
                slot.uploaded
                  ? 'border-sw-primary bg-[#f1f7ff] text-sw-primary'
                  : 'border-[#ffe1a6] bg-[#fff8e8] text-[#9a6700]'
              "
            >
              <span>{{ materialShortName(slot.materialType) }}</span>
            </div>
          </div>
        </PageCard>

        <PageCard title="任务信息" compact>
          <dl class="m-0 grid [grid-template-columns:86px_1fr] gap-x-4 gap-y-[13px]">
            <dt class="font-bold text-sw-muted">任务状态</dt>
            <dd class="m-0 min-w-0"><StatusTag :status="task.status" /></dd>
            <dt class="font-bold text-sw-muted">任务 ID</dt>
            <dd class="m-0 min-w-0"><code>{{ inputTaskId }}</code></dd>
            <dt class="font-bold text-sw-muted">会话 ID</dt>
            <dd class="m-0 min-w-0"><code>{{ inputSessionId }}</code></dd>
            <dt class="font-bold text-sw-muted">材料提交情况</dt>
            <dd class="m-0 min-w-0"><TaskMaterialSummary :slots="task.materials" variant="stacked" /></dd>
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
          />

          <div v-if="task.requiresManualReview" class="sw-alert sw-alert-warning mb-4">
            {{ task.manualReviewNotice || '审核结果中存在阻断性问题或模型/系统异常，请人工复核后继续办理。' }}
          </div>

          <FailureInfo
            v-if="task.status === 'FAILED' || task.failureCategory"
            :failureCategory="task.failureCategory"
            :failureReason="task.failureReason"
          />

          <div v-if="Object.keys(task.extractedFields).length" class="mt-[18px] border-t border-sw-line pt-[18px]">
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

          <div v-if="task.riskHints.length" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">风险提示</h3>
            <ul class="m-0 grid list-none gap-2.5 p-0">
              <li v-for="hint in task.riskHints" :key="hint" class="rounded-lg border-l-4 border-sw-warning bg-[#fff8e8] px-3 py-2.5 leading-[1.7] text-[#714b00]">
                {{ hint }}
              </li>
            </ul>
          </div>

          <div v-if="task.draftOpinion" class="mt-[18px] border-t border-sw-line pt-[18px]">
            <h3 class="mb-3 text-base font-black text-[#16233b]">审核意见草稿</h3>
            <p class="whitespace-pre-wrap rounded-[10px] bg-[#f6f9fd] p-[14px] leading-[1.8] text-slate-700">{{ task.draftOpinion }}</p>
            <small class="mt-2 inline-block text-sw-warning">草稿仅供审批人员参考，不构成最终审批决定。</small>
          </div>
        </PageCard>

        <div class="grid gap-4 [grid-template-columns:repeat(2,minmax(0,1fr))] max-md:grid-cols-1">
          <router-link class="sw-btn sw-btn-ghost" to="/apply">返回申请</router-link>
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
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getReviewerResult, getTaskStatus, toReviewerResultView } from '@/api/task'
import type { MaterialType, ReviewerResultView, Severity } from '@/types'
import { MATERIAL_LABELS } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import StatusBanner from '@/components/business/StatusBanner.vue'
import FailureInfo from '@/components/business/FailureInfo.vue'
import TaskMaterialSummary from '@/components/business/TaskMaterialSummary.vue'

const route = useRoute()

const inputTaskId = ref((route.query.taskId as string) || '')
const inputSessionId = ref((route.query.sessionId as string) || '')
const task = ref<ReviewerResultView | null>(null)
const loading = ref(false)
const lookupError = ref('')

const uploadedCount = computed(() => task.value?.materials.filter((slot) => slot.uploaded).length ?? 0)

const summaryText = computed(() => {
  if (!task.value) return ''
  if (task.value.failureCategory || task.value.status === 'FAILED') return '处理失败或模型结果异常，需人工复核。'
  if (task.value.requiresManualReview) return '结果已生成，但存在阻断项或人工复核提示。'
  if (task.value.status === 'PARTIAL_SUCCESS') return '已生成部分结果，请结合缺失材料和风险提示判断。'
  if (task.value.status === 'COMPLETED') return '后端已返回审核辅助结果，可查看字段、问题和草稿意见。'
  return '任务尚未完成，请稍后重新查询。'
})

async function lookup() {
  if (!inputTaskId.value.trim() || !inputSessionId.value.trim()) {
    lookupError.value = '请输入任务 ID 和会话 ID。'
    return
  }

  lookupError.value = ''
  loading.value = true
  try {
    const [statusRes, resultRes] = await Promise.all([
      getTaskStatus(inputTaskId.value.trim(), inputSessionId.value.trim()),
      getReviewerResult(inputTaskId.value.trim(), inputSessionId.value.trim()),
    ])
    task.value = toReviewerResultView(statusRes.data.data, resultRes.data.data)
  } catch (error) {
    lookupError.value = error instanceof Error ? error.message : '查询失败，请确认任务 ID 和会话 ID。'
    task.value = null
  } finally {
    loading.value = false
  }
}

function materialShortName(type: MaterialType): string {
  return MATERIAL_LABELS[type].slice(0, 2)
}

function severityDotClass(severity: Severity): string {
  if (severity === 'BLOCKER') return 'bg-sw-danger'
  if (severity === 'WARNING') return 'bg-sw-warning'
  return 'bg-sw-info'
}

function severityIcon(severity: Severity): string {
  if (severity === 'BLOCKER') return '!'
  if (severity === 'WARNING') return '△'
  return 'i'
}

if (inputTaskId.value && inputSessionId.value) {
  lookup()
}
</script>
