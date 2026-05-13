<template>
  <div
    class="relative grid items-center gap-5 rounded-[10px] border p-[18px] max-md:grid-cols-1"
    :class="slotStateClasses"
  >
    <input
      :id="inputId"
      type="file"
      class="pointer-events-none absolute h-px w-px opacity-0"
      :accept="accept"
      @change="onChange"
    />

    <div class="grid gap-1.5">
      <strong class="text-[15px] text-[#12213a]">{{ label }}</strong>
      <span class="text-xs text-sw-muted">{{ description }}</span>
    </div>

    <div v-if="file" class="flex min-w-0 items-center gap-3 rounded-[9px] bg-[#f6f9fd] p-3">
      <span class="grid h-11 w-11 place-items-center rounded-[10px] bg-[linear-gradient(135deg,#1677ff,#55a6ff)] text-[11px] font-black text-white">
        {{ fileExt }}
      </span>
      <div class="grid min-w-0 flex-1 gap-1">
        <strong class="truncate text-slate-800">{{ file.name }}</strong>
        <span class="text-xs text-sw-muted">{{ formatSize(file.size) }}</span>
      </div>
      <button type="button" class="bg-transparent font-bold text-sw-danger" @click="emit('clear')">移除</button>
    </div>

    <label
      v-else
      class="grid min-h-[88px] place-items-center gap-2 rounded-[9px] font-extrabold text-sw-primary transition-all duration-200 ease-out hover:-translate-y-px hover:bg-[rgba(22,119,255,0.07)]"
      :for="inputId"
    >
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <path d="M17 8l-5-5-5 5"/>
        <path d="M12 3v12"/>
      </svg>
      <span>点击上传</span>
    </label>

    <p v-if="error" class="col-span-full text-[13px] text-sw-danger">{{ error }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MaterialType } from '@/types'

interface Props {
  materialType: MaterialType
  label: string
  file: File | null
  error: string
  accept: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  change: [event: Event]
  clear: []
}>()

const inputId = computed(() => `file-${props.materialType}`)
const description = computed(() => '支持 jpg / jpeg / png / pdf，单槽位最多 1 个文件')
const fileExt = computed(() => props.file?.name.split('.').pop()?.toUpperCase() || 'FILE')

const slotStateClasses = computed(() => {
  if (props.error) {
    return 'grid-cols-[minmax(180px,1fr)_minmax(220px,1.2fr)] border-[#ffb4ae] bg-[#fff7f6]'
  }
  if (props.file) {
    return 'grid-cols-[minmax(180px,1fr)_minmax(220px,1.2fr)] border-solid border-[#cfe1f7] bg-white'
  }
  return 'grid-cols-[minmax(180px,1fr)_minmax(220px,1.2fr)] border-dashed border-[#b9d8ff] bg-[linear-gradient(180deg,#fbfdff_0%,#f5f9ff_100%)]'
})

function onChange(event: Event) {
  emit('change', event)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
