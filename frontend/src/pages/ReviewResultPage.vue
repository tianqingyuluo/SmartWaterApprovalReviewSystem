<template>
  <div class="review-result-page">
    <div class="page-header-bar">
      <h1 class="page-title">审核辅助结果</h1>
      <div v-if="!task" class="task-lookup">
        <input
          v-model="inputTaskId"
          class="task-input"
          placeholder="输入任务 ID"
          @keyup.enter="lookup"
        />
        <input
          v-model="inputSessionId"
          class="task-input"
          placeholder="输入会话 ID"
          @keyup.enter="lookup"
        />
        <button class="btn-primary" @click="lookup" :disabled="loading">
          {{ loading ? '查询中...' : '查询' }}
        </button>
      </div>
      <p v-if="lookupError" class="lookup-error">{{ lookupError }}</p>
    </div>

    <!-- Status Banner with enhanced states -->
    <StatusBanner v-if="task" :status="task.status" :resultSummary="task.summary" />

    <!-- Manual review warning for COMPLETED with BLOCKER -->
    <div v-if="task && task.status === 'COMPLETED' && task.requiresManualReview" class="manual-review-banner">
      <div class="manual-review-icon">⚠</div>
      <div class="manual-review-content">
        <h3>结果已生成，但需人工复核</h3>
        <p v-if="task.manualReviewNotice">{{ task.manualReviewNotice }}</p>
        <p v-else>审核结果中存在阻断性问题，请人工复核后继续办理。</p>
      </div>
    </div>

    <div v-if="task && (task.status === 'COMPLETED' || task.status === 'PARTIAL_SUCCESS')" class="result-body">
      <MaterialSlotSummary :slots="task.materials" />

      <FieldExtraction
        v-if="Object.keys(task.extractedFields).length"
        :fields="task.extractedFields"
        :confidence="task.fieldConfidence"
      />

      <FindingList
        v-if="task.findings?.length"
        :findings="task.findings"
      />

      <MaterialSummary
        v-if="Object.keys(task.materialSummaries).length"
        :summaries="task.materialSummaries"
      />

      <RiskHints
        v-if="task.riskHints?.length"
        :hints="task.riskHints"
      />

      <DraftOpinion
        v-if="task.draftOpinion"
        :opinion="task.draftOpinion"
      />

      <ManualReviewNotice
        v-if="task.manualReviewNotice && !task.requiresManualReview"
        :notice="task.manualReviewNotice"
      />
    </div>

    <div v-if="task && task.status === 'FAILED'" class="failure-block">
      <FailureInfo :failureCategory="task.failureCategory" :failureReason="task.failureReason" />
    </div>

    <div v-if="task && task.status === 'PARTIAL_SUCCESS'" class="partial-warning">
      <p>部分材料或处理步骤失败，结果可能不完整。请检查材料状态。</p>
    </div>

    <div class="disclaimer">
      <p>本系统提供 AI 辅助审核建议，最终审核结果以审批机关决定为准。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { getTaskStatus, getReviewerResult, toReviewerResultView } from '@/api/task'
import type { ReviewerResultView } from '@/types'
import StatusBanner from '@/components/business/StatusBanner.vue'
import MaterialSlotSummary from '@/components/business/MaterialSlotSummary.vue'
import FieldExtraction from '@/components/business/FieldExtraction.vue'
import FindingList from '@/components/business/FindingList.vue'
import MaterialSummary from '@/components/business/MaterialSummary.vue'
import RiskHints from '@/components/business/RiskHints.vue'
import DraftOpinion from '@/components/business/DraftOpinion.vue'
import ManualReviewNotice from '@/components/business/ManualReviewNotice.vue'
import FailureInfo from '@/components/business/FailureInfo.vue'

const route = useRoute()

const inputTaskId = ref((route.query.taskId as string) || '')
const inputSessionId = ref((route.query.sessionId as string) || '')
const task = ref<ReviewerResultView | null>(null)
const loading = ref(false)
const lookupError = ref('')

async function lookup() {
  if (!inputTaskId.value || !inputSessionId.value) {
    lookupError.value = '请输入任务 ID 和会话 ID'
    return
  }

  lookupError.value = ''
  loading.value = true
  try {
    const [statusRes, resultRes] = await Promise.all([
      getTaskStatus(inputTaskId.value, inputSessionId.value),
      getReviewerResult(inputTaskId.value, inputSessionId.value),
    ])
    task.value = toReviewerResultView(statusRes.data.data, resultRes.data.data)
  } catch (e) {
    lookupError.value = e instanceof Error ? e.message : '查询失败'
    task.value = null
  } finally {
    loading.value = false
  }
}

if (inputTaskId.value && inputSessionId.value) {
  lookup()
}
</script>

<style scoped>
.review-result-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header-bar {
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin: 0 0 16px 0;
}

.task-lookup {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.task-input {
  flex: 1;
  min-width: 200px;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}

.task-input:focus {
  outline: none;
  border-color: #1890ff;
}

.btn-primary {
  padding: 8px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-primary:disabled {
  background: #91d5ff;
  cursor: not-allowed;
}

.lookup-error {
  color: #ff4d4f;
  margin-top: 8px;
  font-size: 14px;
}

.result-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.manual-review-banner {
  display: flex;
  gap: 12px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.manual-review-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.manual-review-content h3 {
  font-size: 15px;
  color: #fa8c16;
  margin: 0 0 4px 0;
}

.manual-review-content p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.failure-block {
  margin-bottom: 16px;
}

.partial-warning {
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
  color: #fa8c16;
  font-size: 14px;
}

.disclaimer {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  color: #bbb;
}
</style>
