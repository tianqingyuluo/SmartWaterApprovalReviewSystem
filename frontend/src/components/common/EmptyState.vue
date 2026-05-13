<template>
  <div class="grid justify-items-center gap-2.5 px-[18px] py-11 text-center text-sw-muted">
    <div class="grid h-[68px] w-[68px] place-items-center rounded-[22px] bg-[#f3f8ff] text-[#94aed0]" aria-hidden="true">
      <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <path d="M14 2v6h6"/>
        <path d="M9 13h6"/>
        <path d="M9 17h4"/>
      </svg>
    </div>
    <h3 class="text-base text-slate-700">{{ title }}</h3>
    <p v-if="description" class="max-w-[420px] leading-[1.7]">{{ description }}</p>
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
