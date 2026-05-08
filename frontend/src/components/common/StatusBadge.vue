<template>
  <span class="status-badge" :class="statusClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus } from '@/types'
import { STATUS_LABELS_APPLICANT, STATUS_LABELS_REVIEWER } from '@/types'

interface Props {
  status: ProcessingStatus
  audience?: 'applicant' | 'reviewer'
}

const props = withDefaults(defineProps<Props>(), {
  audience: 'applicant',
})

const label = computed(() =>
  props.audience === 'reviewer'
    ? STATUS_LABELS_REVIEWER[props.status]
    : STATUS_LABELS_APPLICANT[props.status],
)

const statusClass = computed(() => {
  switch (props.status) {
    case 'COMPLETED':
      return 'status-completed'
    case 'PARTIAL_SUCCESS':
      return 'status-partial'
    case 'FAILED':
      return 'status-failed'
    case 'PROCESSING':
    case 'QUEUED':
      return 'status-processing'
    default:
      return 'status-submitted'
  }
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-partial {
  background: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.status-failed {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.status-processing {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.status-submitted {
  background: #f5f5f5;
  color: #999;
  border: 1px solid #d9d9d9;
}
</style>
