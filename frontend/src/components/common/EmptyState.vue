<template>
  <div class="empty-state">
    <div class="empty-icon" aria-hidden="true">
      <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <path d="M14 2v6h6"/>
        <path d="M9 13h6"/>
        <path d="M9 17h4"/>
      </svg>
    </div>
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  description: '',
})
</script>

<style scoped>
.empty-state {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 44px 18px;
  text-align: center;
  color: var(--sw-muted);
}

.empty-icon {
  display: grid;
  width: 68px;
  height: 68px;
  place-items: center;
  border-radius: 22px;
  background: #f3f8ff;
  color: #94aed0;
}

.empty-state h3 {
  color: #334155;
  font-size: 16px;
}

.empty-state p {
  max-width: 420px;
  line-height: 1.7;
}
</style>
