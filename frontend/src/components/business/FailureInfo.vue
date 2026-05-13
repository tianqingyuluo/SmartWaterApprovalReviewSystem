<template>
  <div class="rounded-lg border border-[#ffccc7] bg-[#fff2f0] p-6">
    <h3 class="mb-3 text-base text-[#ff4d4f]">处理失败</h3>
    <p v-if="categoryLabel" class="mb-2 text-sm font-medium text-[#ff4d4f]">{{ categoryLabel }}</p>
    <p v-if="failureReason" class="mb-3 text-sm text-[#666]">{{ failureReason }}</p>
    <p class="text-[13px] text-[#999]">请检查材料文件是否可读，或重新提交新的任务。</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FAILURE_CATEGORY_LABELS } from '@/types'
import type { FailureCategory } from '@/types'

interface Props {
  failureCategory: FailureCategory
  failureReason: string | null
}

const props = defineProps<Props>()

const categoryLabel = computed(() =>
  props.failureCategory ? FAILURE_CATEGORY_LABELS[props.failureCategory] : '处理异常',
)
</script>
