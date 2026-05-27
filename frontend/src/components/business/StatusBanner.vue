<template>
  <div class="mb-5 rounded-lg border px-5 py-4" :class="bannerClass">
    <div class="mb-2 text-base font-semibold">{{ label }}</div>
    <div v-if="resultSummary" class="flex flex-wrap gap-3 text-[13px]">
      <span v-if="resultSummary.blockerCount" class="text-[#ff4d4f]">
        阻断: {{ resultSummary.blockerCount }}
      </span>
      <span v-if="resultSummary.warningCount" class="text-[#fa8c16]">
        警告: {{ resultSummary.warningCount }}
      </span>
      <span v-if="resultSummary.infoCount" class="text-[#1890ff]">
        提示: {{ resultSummary.infoCount }}
      </span>
      <span class="text-[#666]">共 {{ resultSummary.totalFindings }} 项</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus, ResultSummary } from '@/types'
import { STATUS_LABELS_APPLICANT, STATUS_LABELS_REVIEWER } from '@/types'

interface Props {
  status: ProcessingStatus
  resultSummary: ResultSummary | null
  requiresManualReview?: boolean
  audience?: 'APPLICANT' | 'REVIEWER'
}

const props = defineProps<Props>()

const label = computed(() => {
  if (props.audience === 'APPLICANT') {
    return STATUS_LABELS_APPLICANT[props.status]
  }
  if (props.status === 'COMPLETED' && props.requiresManualReview) {
    return '审核辅助结果已生成，需人工复核'
  }
  return STATUS_LABELS_REVIEWER[props.status]
})

const bannerClass = computed(() => {
  switch (props.status) {
    case 'COMPLETED':
      return 'bg-[#f6ffed] border-[#b7eb8f]'
    case 'PARTIAL_SUCCESS':
      return 'bg-[#fff7e6] border-[#ffd591]'
    case 'FAILED':
      return 'bg-[#fff2f0] border-[#ffccc7]'
    case 'PROCESSING':
    case 'QUEUED':
      return 'bg-[#e6f7ff] border-[#91d5ff]'
    default:
      return ''
  }
})
</script>
