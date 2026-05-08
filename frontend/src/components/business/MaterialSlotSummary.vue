<template>
  <section class="card">
    <h2>材料提交概况</h2>
    <table class="material-table">
      <thead>
        <tr>
          <th>材料类型</th>
          <th>文件名</th>
          <th>大小</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="slot in sortedSlots" :key="slot.materialType">
          <td>{{ MATERIAL_LABELS[slot.materialType] || slot.materialType }}</td>
          <td>{{ slot.originalFileName || '—' }}</td>
          <td>{{ slot.fileSize ? formatSize(slot.fileSize) : '—' }}</td>
          <td>
            <span v-if="slot.originalFileName" class="tag-uploaded">已上传</span>
            <span v-else class="tag-missing">缺失</span>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MaterialSlot } from '@/types'
import { MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'

interface Props {
  slots: MaterialSlot[]
}

const props = defineProps<Props>()

const sortedSlots = computed(() => {
  const order = [...MATERIAL_SLOTS]
  return [...props.slots].sort(
    (a, b) => order.indexOf(a.materialType) - order.indexOf(b.materialType),
  )
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
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

.material-table {
  width: 100%;
  border-collapse: collapse;
}

.material-table th,
.material-table td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.material-table th {
  background: #fafafa;
  font-weight: 600;
  color: #666;
}

.tag-uploaded {
  color: #52c41a;
  font-size: 13px;
}

.tag-missing {
  color: #fa8c16;
  font-size: 13px;
}
</style>
