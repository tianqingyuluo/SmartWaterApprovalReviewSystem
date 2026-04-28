<template>
  <section class="card">
    <h2>风险提示</h2>
    <ul class="risk-list">
      <li v-for="(hint, idx) in hints" :key="idx" class="risk-item">
        {{ hint }}
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
interface Props {
  hints: string[]
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
  color: #fa8c16;
}

.risk-list {
  list-style: disc;
  padding-left: 20px;
}

.risk-item {
  font-size: 14px;
  margin-bottom: 6px;
  color: #555;
  line-height: 1.6;
}
</style>
