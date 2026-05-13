<template>
  <div class="flex flex-wrap gap-[7px]" :class="variant === 'stacked' ? 'grid gap-[10px]' : ''">
    <span
      v-for="slot in normalizedSlots"
      :key="slot.materialType"
      class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-bold"
      :class="
        slot.uploaded
          ? 'border-[#bbf0d4] bg-[#eefcf5] text-[#087443]'
          : 'border-[#ffe1a6] bg-[#fff8e8] text-[#9a6700]'
      "
      :title="chipTitle(slot)"
    >
      <span class="h-[7px] w-[7px] rounded-full bg-current" aria-hidden="true"></span>
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
