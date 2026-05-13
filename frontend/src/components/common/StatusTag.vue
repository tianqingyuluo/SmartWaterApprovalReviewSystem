<template>
  <span class="status-tag" :style="tagStyle">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ProcessingStatus } from '@/types'
import { STATUS_LABELS_APPLICANT, STATUS_TAG_COLORS } from '@/types'

interface Props {
  status: ProcessingStatus
}

const props = defineProps<Props>()

const label = computed(() => STATUS_LABELS_APPLICANT[props.status])

const tagStyle = computed(() => {
  const colors = STATUS_TAG_COLORS[props.status]
  return {
    backgroundColor: colors.bg,
    color: colors.text,
    borderColor: colors.border,
  }
})
</script>

<style scoped>
.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid;
  white-space: nowrap;
}
</style>
