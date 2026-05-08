<template>
  <section class="card notice-card">
    <h2>人工复核提示</h2>
    <p>{{ notice }}</p>
  </section>
</template>

<script setup lang="ts">
interface Props {
  notice: string
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

.notice-card {
  background: #fffbe6;
  border: 1px solid #ffe58f;
}

.notice-card h2 {
  font-size: 16px;
  margin-bottom: 8px;
  color: #d48806;
}

.notice-card p {
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}
</style>
