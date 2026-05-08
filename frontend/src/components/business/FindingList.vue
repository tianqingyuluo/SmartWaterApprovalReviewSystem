<template>
  <section class="card">
    <h2>问题清单</h2>
    <div v-for="(finding, idx) in findings" :key="idx" class="finding-item" :class="severityClass(finding.severity)">
      <div class="finding-header">
        <span class="severity-tag" :class="'tag-' + severityClass(finding.severity)">
          {{ severityLabel(finding.severity) }}
        </span>
        <span class="finding-type">{{ finding.findingType }}</span>
      </div>
      <p class="finding-desc">{{ finding.description }}</p>
      <p v-if="finding.basis" class="finding-basis">依据: {{ finding.basis }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Finding } from '@/types'

interface Props {
  findings: Finding[]
}

defineProps<Props>()

function severityClass(severity: string): string {
  if (severity === 'BLOCKER') return 'blocker'
  if (severity === 'WARNING') return 'warning'
  return 'info'
}

function severityLabel(severity: string): string {
  if (severity === 'BLOCKER') return '阻断'
  if (severity === 'WARNING') return '警告'
  return '提示'
}
</script>

<style scoped>
.card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
}

.card h2 {
  font-size: 16px;
  margin-bottom: 12px;
}

.finding-item {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.finding-item.blocker {
  background: #fff2f0;
  border: 1px solid #ffccc7;
}

.finding-item.warning {
  background: #fff7e6;
  border: 1px solid #ffd591;
}

.finding-item.info {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
}

.finding-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.severity-tag {
  padding: 1px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 500;
}

.tag-blocker {
  background: #ff4d4f;
  color: #fff;
}

.tag-warning {
  background: #fa8c16;
  color: #fff;
}

.tag-info {
  background: #ddd;
  color: #666;
}

.finding-type {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.finding-desc {
  font-size: 14px;
  margin-top: 4px;
}

.finding-basis {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
