<template>
  <section
    class="rounded-sw border border-[rgba(213,224,236,0.85)] bg-sw-card shadow-sw-card"
    :class="compact ? 'px-5 py-[18px]' : 'px-7 py-6 max-md:px-4 max-md:py-[18px]'"
  >
    <header
      v-if="title || $slots.extra"
      class="mb-5 flex items-start justify-between gap-4 max-md:block"
    >
      <div>
        <h2 v-if="title" class="relative pl-3 text-[17px] font-extrabold leading-[1.3] text-[#152238] before:absolute before:left-0 before:top-0.5 before:h-[18px] before:w-[3px] before:rounded-[3px] before:bg-sw-primary">
          {{ title }}
        </h2>
        <p v-if="subtitle" class="mt-1.5 text-[13px] leading-[1.6] text-sw-muted">{{ subtitle }}</p>
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
