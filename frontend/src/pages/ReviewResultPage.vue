<template>
  <div class="sw-page review-result-page">
    <div class="result-heading">
      <div>
        <h1 class="sw-page-title">AI 智能审核结果</h1>
        <p>AI 结果用于审批辅助；存在失败、阻断项或人工复核提示时，不视为完整通过。</p>
      </div>
      <router-link class="sw-btn sw-btn-ghost" to="/">返回申请列表</router-link>
    </div>

    <PageCard v-if="!task" title="查询任务" subtitle="请输入任务 ID 和会话 ID。MVP 无账号体系，因此不能声明已按用户权限隔离。" compact>
      <div class="lookup-row">
        <input v-model="inputTaskId" class="sw-input" placeholder="任务 ID" @keyup.enter="lookup" />
        <input v-model="inputSessionId" class="sw-input" placeholder="会话 ID" @keyup.enter="lookup" />
        <button type="button" class="sw-btn sw-btn-primary" :disabled="loading" @click="lookup">
          {{ loading ? '查询中...' : '查询' }}
        </button>
      </div>
      <p v-if="lookupError" class="lookup-error">{{ lookupError }}</p>
    </PageCard>

    <div v-if="loading && !task" class="sw-alert sw-alert-info loading-line">
      <span class="sw-spinner"></span>
      <span>正在读取任务状态和 AI 初审结果</span>
    </div>

    <div v-if="task" class="result-layout">
      <section class="left-pane">
        <PageCard compact class="viewer-card">
          <div class="viewer-toolbar">
            <span></span>
            <strong>材料与任务信息</strong>
            <small>{{ uploadedCount }}/{{ task.materials.length }} 已提交</small>
          </div>
          <div class="viewer-placeholder">
            <div class="document-glyph" aria-hidden="true">
              <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <path d="M14 2v6h6"/>
                <path d="M8 13h8"/>
                <path d="M8 17h5"/>
              </svg>
            </div>
            <h2>不提供伪造证照预览</h2>
            <p>当前后端返回材料元数据与抽取结果，未返回可安全嵌入的 PDF/图片预览地址。</p>
          </div>
          <div class="thumbnail-strip">
            <div v-for="slot in task.materials" :key="slot.materialType" class="thumbnail" :class="{ uploaded: slot.uploaded }">
              <span>{{ materialShortName(slot.materialType) }}</span>
            </div>
          </div>
        </PageCard>

        <PageCard title="任务信息" compact>
          <dl class="task-meta">
            <dt>任务状态</dt>
            <dd><StatusTag :status="task.status" /></dd>
            <dt>任务 ID</dt>
            <dd><code>{{ inputTaskId }}</code></dd>
            <dt>会话 ID</dt>
            <dd><code>{{ inputSessionId }}</code></dd>
            <dt>材料提交情况</dt>
            <dd><TaskMaterialSummary :slots="task.materials" variant="stacked" /></dd>
          </dl>
        </PageCard>
      </section>

      <section class="right-pane">
        <PageCard compact class="analysis-card">
          <div class="analysis-head">
            <div>
              <h2>AI 分析面板</h2>
              <p>{{ summaryText }}</p>
            </div>
            <div class="ai-orb" aria-hidden="true">AI</div>
          </div>

          <StatusBanner
            :status="task.status"
            :resultSummary="task.summary"
            :requiresManualReview="task.requiresManualReview"
          />

          <div v-if="task.requiresManualReview" class="sw-alert sw-alert-warning notice-block">
            {{ task.manualReviewNotice || '审核结果中存在阻断性问题或模型/系统异常，请人工复核后继续办理。' }}
          </div>

          <FailureInfo
            v-if="task.status === 'FAILED' || task.failureCategory"
            :failureCategory="task.failureCategory"
            :failureReason="task.failureReason"
          />

          <div v-if="Object.keys(task.extractedFields).length" class="analysis-section">
            <h3>抽取字段</h3>
            <div class="field-grid">
              <div v-for="(value, key) in task.extractedFields" :key="key" class="field-cell">
                <span>{{ key }}</span>
                <strong>{{ value || '未返回' }}</strong>
              </div>
            </div>
          </div>

          <div class="analysis-section">
            <h3>合规检查清单</h3>
            <div v-if="task.findings.length" class="check-list">
              <article v-for="finding in task.findings" :key="`${finding.findingType}-${finding.description}`" class="check-item" :class="severityClass(finding.severity)">
                <span class="check-mark">{{ severityIcon(finding.severity) }}</span>
                <div>
                  <strong>{{ finding.findingType }}</strong>
                  <p>{{ finding.description }}</p>
                  <small v-if="finding.basis">依据：{{ finding.basis }}</small>
                </div>
              </article>
            </div>
            <EmptyState v-else title="暂无问题清单" description="后端未返回问题项，仍需以人工审批结论为准。" />
          </div>

          <div v-if="task.riskHints.length" class="analysis-section">
            <h3>风险提示</h3>
            <ul class="risk-list">
              <li v-for="hint in task.riskHints" :key="hint">{{ hint }}</li>
            </ul>
          </div>

          <div v-if="task.draftOpinion" class="analysis-section opinion-section">
            <h3>审核意见草稿</h3>
            <p>{{ task.draftOpinion }}</p>
            <small>草稿仅供审批人员参考，不构成最终审批决定。</small>
          </div>
        </PageCard>

        <div class="action-bar">
          <router-link class="sw-btn sw-btn-ghost" to="/apply">返回申请</router-link>
          <button type="button" class="sw-btn sw-btn-ghost" @click="lookup" :disabled="loading">
            {{ loading ? '刷新中...' : '重新查询' }}
          </button>
        </div>
      </section>
    </div>

    <p class="disclaimer">本系统提供 AI 辅助审核建议，最终审核结果以审批机关决定为准。</p>
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

function severityClass(severity: Severity): string {
  if (severity === 'BLOCKER') return 'blocker'
  if (severity === 'WARNING') return 'warning'
  return 'info'
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

<style scoped>
.review-result-page {
  max-width: 1480px;
}

.result-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.result-heading p {
  margin-top: -12px;
  margin-bottom: 22px;
  color: var(--sw-muted);
  line-height: 1.7;
}

.lookup-row {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(220px, 1fr) auto;
  gap: 12px;
}

.lookup-error {
  margin-top: 12px;
  color: var(--sw-danger);
}

.loading-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
}

.result-layout {
  display: grid;
  grid-template-columns: minmax(420px, 1.25fr) minmax(430px, 0.95fr);
  gap: 24px;
  align-items: start;
}

.left-pane,
.right-pane {
  display: grid;
  gap: 16px;
}

.viewer-card {
  padding: 0;
  overflow: hidden;
}

.viewer-toolbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 56px;
  background: linear-gradient(180deg, #1f2933 0%, #111827 100%);
  color: #fff;
  padding: 0 20px;
}

.viewer-toolbar small {
  justify-self: end;
  color: #cbd5e1;
}

.viewer-placeholder {
  display: grid;
  min-height: 455px;
  place-items: center;
  align-content: center;
  gap: 14px;
  background:
    linear-gradient(90deg, rgba(15, 23, 42, 0.035) 1px, transparent 1px),
    linear-gradient(rgba(15, 23, 42, 0.035) 1px, transparent 1px),
    #fbfcff;
  background-size: 24px 24px;
  padding: 44px;
  text-align: center;
}

.document-glyph {
  display: grid;
  width: 116px;
  height: 116px;
  place-items: center;
  border-radius: 28px;
  background: #eef6ff;
  color: #6da9f5;
}

.viewer-placeholder h2 {
  color: #172033;
  font-size: 20px;
}

.viewer-placeholder p {
  max-width: 440px;
  color: var(--sw-muted);
  line-height: 1.8;
}

.thumbnail-strip {
  display: flex;
  gap: 12px;
  border-top: 1px solid var(--sw-line);
  background: #fff;
  padding: 16px 20px;
}

.thumbnail {
  display: grid;
  width: 70px;
  height: 54px;
  place-items: center;
  border: 1px solid #ffe1a6;
  border-radius: 8px;
  background: #fff8e8;
  color: #9a6700;
  font-size: 12px;
  font-weight: 800;
}

.thumbnail.uploaded {
  border-color: var(--sw-primary);
  background: #f1f7ff;
  color: var(--sw-primary);
}

.task-meta {
  display: grid;
  grid-template-columns: 86px 1fr;
  gap: 13px 16px;
  margin: 0;
}

.task-meta dt {
  color: var(--sw-muted);
  font-weight: 700;
}

.task-meta dd {
  min-width: 0;
  margin: 0;
}

.analysis-card {
  overflow: hidden;
}

.analysis-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  border-bottom: 1px solid var(--sw-line);
  margin: -2px -4px 18px;
  padding: 0 0 18px;
}

.analysis-head h2 {
  color: #12213a;
  font-size: 19px;
  font-weight: 900;
}

.analysis-head p {
  margin-top: 8px;
  color: var(--sw-muted);
  line-height: 1.7;
}

.ai-orb {
  display: grid;
  width: 78px;
  height: 78px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 30%, #ffffff, transparent 34%),
    linear-gradient(135deg, #51b3ff, #1677ff 64%, #7ad6ff);
  color: #fff;
  font-size: 25px;
  font-weight: 900;
  box-shadow: 0 0 0 8px rgba(22, 119, 255, 0.08), 0 12px 30px rgba(22, 119, 255, 0.25);
}

.notice-block {
  margin-bottom: 16px;
}

.analysis-section {
  border-top: 1px solid var(--sw-line);
  padding-top: 18px;
  margin-top: 18px;
}

.analysis-section h3 {
  margin-bottom: 12px;
  color: #16233b;
  font-size: 16px;
  font-weight: 900;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field-cell {
  display: grid;
  gap: 6px;
  border-radius: 10px;
  background: #f6f9fd;
  padding: 12px;
}

.field-cell span {
  color: var(--sw-muted);
  font-size: 12px;
}

.field-cell strong {
  min-width: 0;
  overflow-wrap: anywhere;
  color: #20304a;
}

.check-list {
  display: grid;
  gap: 10px;
}

.check-item {
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 10px;
  border-bottom: 1px solid #edf2f7;
  padding: 10px 0;
}

.check-mark {
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.check-item.info .check-mark {
  background: var(--sw-info);
}

.check-item.warning .check-mark {
  background: var(--sw-warning);
}

.check-item.blocker .check-mark {
  background: var(--sw-danger);
}

.check-item strong {
  color: #23405e;
}

.check-item p {
  margin-top: 4px;
  color: #34516f;
  line-height: 1.65;
}

.check-item small {
  display: inline-block;
  margin-top: 5px;
  color: var(--sw-muted);
}

.risk-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.risk-list li {
  border-left: 3px solid var(--sw-warning);
  border-radius: 8px;
  background: #fff8e8;
  color: #714b00;
  line-height: 1.7;
  padding: 10px 12px;
}

.opinion-section p {
  border-radius: 10px;
  background: #f6f9fd;
  color: #334155;
  line-height: 1.8;
  padding: 14px;
  white-space: pre-wrap;
}

.opinion-section small {
  display: inline-block;
  margin-top: 8px;
  color: var(--sw-warning);
}

.action-bar {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.action-note,
.disclaimer {
  color: var(--sw-faint);
  font-size: 12px;
  line-height: 1.7;
  text-align: center;
}

.disclaimer {
  margin-top: 20px;
}

@media (max-width: 1180px) {
  .result-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .result-heading,
  .analysis-head {
    display: block;
  }

  .lookup-row,
  .field-grid,
  .action-bar {
    grid-template-columns: 1fr;
  }

  .ai-orb {
    margin-top: 14px;
  }

  .viewer-toolbar {
    grid-template-columns: 1fr;
    gap: 4px;
    padding: 12px 16px;
    text-align: center;
  }

  .viewer-toolbar small {
    justify-self: center;
  }

  .viewer-placeholder {
    min-height: 300px;
    padding: 28px 18px;
  }
}
</style>
