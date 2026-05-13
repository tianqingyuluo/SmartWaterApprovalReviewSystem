<template>
  <div class="status-banner" :class="bannerClass">
    <div class="status-label">{{ label }}</div>
    <div v-if="resultSummary" class="status-summary">
      <span v-if="resultSummary.blockerCount" class="count blocker">
        阻断: {{ resultSummary.blockerCount }}
      </span>
      <span v-if="resultSummary.warningCount" class="count warning">
        警告: {{ resultSummary.warningCount }}
      </span>
      <span v-if="resultSummary.infoCount" class="count info">
        提示: {{ resultSummary.infoCount }}
      </span>
      <span class="count total">共 {{ resultSummary.totalFindings }} 项</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus, ResultSummary } from '@/types'
import { STATUS_LABELS_REVIEWER } from '@/types'

interface Props {
  status: ProcessingStatus
  resultSummary: ResultSummary | null
  requiresManualReview?: boolean
}

const props = defineProps<Props>()

const label = computed(() => {
  if (props.status === 'COMPLETED' && props.requiresManualReview) {
    return '审核辅助结果已生成，需人工复核'
  }
  return STATUS_LABELS_REVIEWER[props.status]
})

const bannerClass = computed(() => {
  switch (props.status) {
    case 'COMPLETED':
      return 'banner-completed'
    case 'PARTIAL_SUCCESS':
      return 'banner-partial'
    case 'FAILED':
      return 'banner-failed'
    case 'PROCESSING':
    case 'QUEUED':
      return 'banner-processing'
    default:
      return ''
  }
})
</script>

<style scoped>
.status-banner {
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.banner-completed {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.banner-partial {
  background: #fff7e6;
  border: 1px solid #ffd591;
}

.banner-failed {
  background: #fff2f0;
  border: 1px solid #ffccc7;
}

.banner-processing {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
}

.status-label {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.status-summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.count {
  font-size: 13px;
}

.blocker {
  color: #ff4d4f;
}

.warning {
  color: #fa8c16;
}

.info {
  color: #1890ff;
}

.total {
  color: #666;
}
</style>
