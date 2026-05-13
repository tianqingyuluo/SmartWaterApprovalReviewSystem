<template>
  <div class="failure-info">
    <h3>处理失败</h3>
    <p v-if="categoryLabel" class="failure-category">{{ categoryLabel }}</p>
    <p v-if="failureReason" class="failure-reason">{{ failureReason }}</p>
    <p class="failure-hint">请检查材料文件是否可读，或重新提交新的任务。</p>
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

<style scoped>
.failure-info {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  padding: 24px;
}

.failure-info h3 {
  color: #ff4d4f;
  margin-bottom: 12px;
  font-size: 16px;
}

.failure-category {
  font-size: 14px;
  color: #ff4d4f;
  font-weight: 500;
  margin-bottom: 8px;
}

.failure-reason {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.failure-hint {
  font-size: 13px;
  color: #999;
}
</style>
