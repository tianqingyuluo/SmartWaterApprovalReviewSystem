<template>
  <div class="reviewer-page">
    <header class="page-header">
      <h1>审核辅助结果</h1>
      <div class="task-lookup" v-if="!task">
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
        <button class="btn-lookup" @click="lookup" :disabled="loading">
          {{ loading ? '查询中...' : '查询' }}
        </button>
      </div>
      <p v-if="lookupError" class="lookup-error">{{ lookupError }}</p>
    </header>

    <StatusBanner v-if="task" :status="task.status" :resultSummary="task.resultSummary" />

    <div v-if="task && (task.status === 'COMPLETED' || task.status === 'PARTIAL_SUCCESS')" class="result-body">
      <MaterialSlotSummary :slots="task.materialSlots" />

      <FieldExtraction
        v-if="task.reviewerResult?.extractedFields"
        :fields="task.reviewerResult.extractedFields"
        :confidence="task.reviewerResult.fieldConfidence"
      />

      <FindingList
        v-if="task.reviewerResult?.findings?.length"
        :findings="task.reviewerResult.findings"
      />

      <MaterialSummary
        v-if="task.reviewerResult?.materialSummaries"
        :summaries="task.reviewerResult.materialSummaries"
      />

      <RiskHints
        v-if="task.reviewerResult?.riskHints?.length"
        :hints="task.reviewerResult.riskHints"
      />

      <DraftOpinion
        v-if="task.reviewerResult?.draftOpinion"
        :opinion="task.reviewerResult.draftOpinion"
      />

      <ManualReviewNotice
        v-if="task.reviewerResult?.manualReviewNotice"
        :notice="task.reviewerResult.manualReviewNotice"
      />
    </div>

    <div v-if="task && task.status === 'FAILED'" class="failure-block">
      <h3>处理失败</h3>
      <p v-if="task.reviewerResult?.failureReason">{{ task.reviewerResult.failureReason }}</p>
      <p>请检查材料文件是否可读，或重新提交新的任务。</p>
    </div>

    <div class="back-link">
      <router-link to="/">返回提交页</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { getTask } from '@/api/task'
import type { ReviewTask } from '@/types'
import StatusBanner from '@/components/business/StatusBanner.vue'
import MaterialSlotSummary from '@/components/business/MaterialSlotSummary.vue'
import FieldExtraction from '@/components/business/FieldExtraction.vue'
import FindingList from '@/components/business/FindingList.vue'
import MaterialSummary from '@/components/business/MaterialSummary.vue'
import RiskHints from '@/components/business/RiskHints.vue'
import DraftOpinion from '@/components/business/DraftOpinion.vue'
import ManualReviewNotice from '@/components/business/ManualReviewNotice.vue'

const route = useRoute()

const inputTaskId = ref((route.query.taskId as string) || '')
const inputSessionId = ref((route.query.sessionId as string) || '')
const task = ref<ReviewTask | null>(null)
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
    const res = await getTask(inputTaskId.value, inputSessionId.value)
    task.value = res.data.data
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
.reviewer-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 16px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  margin-bottom: 16px;
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

.btn-lookup {
  padding: 8px 24px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-lookup:hover {
  background: #40a9ff;
}

.btn-lookup:disabled {
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

.failure-block {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  padding: 24px;
}

.failure-block h3 {
  color: #ff4d4f;
  margin-bottom: 8px;
}

.back-link {
  margin-top: 32px;
  text-align: center;
}

.back-link a {
  color: #1890ff;
  font-size: 14px;
}
</style>
