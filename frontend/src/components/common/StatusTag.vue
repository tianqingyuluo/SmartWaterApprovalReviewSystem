<template>
  <span class="inline-block whitespace-nowrap rounded-xl border px-2.5 py-0.5 text-xs font-medium" :style="tagStyle">{{ label }}</span>
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
