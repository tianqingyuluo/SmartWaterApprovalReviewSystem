<template>
  <section class="page-card" :class="{ compact }">
    <header v-if="title || $slots.extra" class="card-head">
      <div>
        <h2 v-if="title">{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <slot name="extra" />
    </header>
    <slot />
  </section>
</template>

<script setup lang="ts">
interface Props {
  title?: string
  subtitle?: string
  compact?: boolean
}

withDefaults(defineProps<Props>(), {
  title: '',
  subtitle: '',
  compact: false,
})
</script>

<style scoped>
.page-card {
  border: 1px solid rgba(213, 224, 236, 0.85);
  border-radius: var(--sw-radius);
  background: var(--sw-card);
  box-shadow: var(--sw-shadow);
  padding: 24px 28px;
}

.page-card.compact {
  padding: 18px 20px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.card-head h2 {
  position: relative;
  color: #152238;
  font-size: 17px;
  font-weight: 800;
  line-height: 1.3;
  padding-left: 12px;
}

.card-head h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: 2px;
  width: 3px;
  height: 18px;
  border-radius: 3px;
  background: var(--sw-primary);
}

.card-head p {
  margin-top: 6px;
  color: var(--sw-muted);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .page-card {
    padding: 18px 16px;
  }

  .card-head {
    display: block;
  }
}
</style>
