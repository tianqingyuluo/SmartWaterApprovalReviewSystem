<template>
  <div class="upload-slot" :class="{ filled: Boolean(file), invalid: Boolean(error) }">
    <input
      :id="inputId"
      type="file"
      class="file-input"
      :accept="accept"
      @change="onChange"
    />

    <div class="slot-copy">
      <strong>{{ label }}</strong>
      <span>{{ description }}</span>
    </div>

    <div v-if="file" class="file-preview">
      <span class="file-type">{{ fileExt }}</span>
      <div class="file-meta">
        <strong>{{ file.name }}</strong>
        <span>{{ formatSize(file.size) }}</span>
      </div>
      <button type="button" class="remove-btn" @click="emit('clear')">移除</button>
    </div>

    <label v-else class="upload-action" :for="inputId">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <path d="M17 8l-5-5-5 5"/>
        <path d="M12 3v12"/>
      </svg>
      <span>点击上传</span>
    </label>

    <p v-if="error" class="slot-error">{{ error }}</p>
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

function onChange(event: Event) {
  emit('change', event)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.upload-slot {
  position: relative;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(220px, 1.2fr);
  align-items: center;
  gap: 20px;
  border: 1px dashed #b9d8ff;
  border-radius: 10px;
  background: linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
  padding: 18px;
}

.upload-slot.invalid {
  border-color: #ffb4ae;
  background: #fff7f6;
}

.upload-slot.filled {
  border-style: solid;
  border-color: #cfe1f7;
  background: #fff;
}

.file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.slot-copy {
  display: grid;
  gap: 6px;
}

.slot-copy strong {
  color: #12213a;
  font-size: 15px;
}

.slot-copy span {
  color: var(--sw-muted);
  font-size: 12px;
}

.upload-action {
  display: grid;
  min-height: 88px;
  place-items: center;
  gap: 8px;
  border-radius: 9px;
  color: var(--sw-primary);
  font-weight: 800;
  transition: background 0.18s ease, transform 0.18s ease;
}

.upload-action:hover {
  background: rgba(22, 119, 255, 0.07);
  transform: translateY(-1px);
}

.file-preview {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
  border-radius: 9px;
  background: #f6f9fd;
  padding: 12px;
}

.file-type {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 10px;
  background: linear-gradient(135deg, #1677ff, #55a6ff);
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.file-meta {
  display: grid;
  min-width: 0;
  flex: 1;
  gap: 4px;
}

.file-meta strong {
  overflow: hidden;
  color: #1f2937;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta span {
  color: var(--sw-muted);
  font-size: 12px;
}

.remove-btn {
  border: 0;
  background: transparent;
  color: var(--sw-danger);
  font-weight: 700;
}

.slot-error {
  grid-column: 1 / -1;
  color: var(--sw-danger);
  font-size: 13px;
}

@media (max-width: 760px) {
  .upload-slot {
    grid-template-columns: 1fr;
  }
}
</style>
