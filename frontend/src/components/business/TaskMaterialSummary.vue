<template>
  <div class="material-summary" :class="variant">
    <span
      v-for="slot in normalizedSlots"
      :key="slot.materialType"
      class="material-chip"
      :class="{ uploaded: slot.uploaded }"
      :title="chipTitle(slot)"
    >
      <span class="chip-dot" aria-hidden="true"></span>
      <span>{{ MATERIAL_LABELS[slot.materialType] }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MaterialSlot } from '@/types'
import { MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'

interface Props {
  slots: MaterialSlot[]
  variant?: 'compact' | 'stacked'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'compact',
})

const normalizedSlots = computed(() =>
  MATERIAL_SLOTS.map((materialType) => {
    const found = props.slots.find((slot) => slot.materialType === materialType)
    return found ?? {
      materialType,
      originalFileName: null,
      uploaded: false,
    }
  }),
)

function chipTitle(slot: MaterialSlot) {
  return `${MATERIAL_LABELS[slot.materialType]}：${slot.uploaded ? slot.originalFileName || '已上传' : '未上传'}`
}
</script>

<style scoped>
.material-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.material-summary.stacked {
  display: grid;
  gap: 10px;
}

.material-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #ffe1a6;
  border-radius: 999px;
  background: #fff8e8;
  color: #9a6700;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.material-chip.uploaded {
  border-color: #bbf0d4;
  background: #eefcf5;
  color: #087443;
}

.chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}
</style>
