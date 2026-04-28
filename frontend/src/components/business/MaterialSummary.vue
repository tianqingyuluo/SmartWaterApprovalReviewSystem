<template>
  <section class="card">
    <h2>材料摘要</h2>
    <div v-for="(summary, type) in summaries" :key="type" class="summary-item">
      <h3>{{ MATERIAL_LABELS[type as MaterialType] || type }}</h3>
      <p>{{ summary }}</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { MATERIAL_LABELS, type MaterialType } from '@/types'

interface Props {
  summaries: Record<string, string>
}

defineProps<Props>()
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

.summary-item {
  margin-bottom: 12px;
}

.summary-item h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.summary-item p {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}
</style>
