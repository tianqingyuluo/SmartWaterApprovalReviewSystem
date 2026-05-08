<template>
  <section class="card">
    <h2>审核意见草稿</h2>
    <div class="opinion-text">{{ opinion }}</div>
    <p class="opinion-disclaimer">以上为 AI 辅助建议，不作为最终审批判定。</p>
  </section>
</template>

<script setup lang="ts">
interface Props {
  opinion: string
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

.opinion-text {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}

.opinion-disclaimer {
  margin-top: 12px;
  font-size: 12px;
  color: #fa8c16;
  font-style: italic;
}
</style>
