<template>
  <section
    v-if="notice"
    class="border shadow-[0_10px_24px_rgba(15,23,42,0.05)]"
    :class="[notice.wrapperClass, compact ? 'rounded-lg px-3 py-2.5' : 'rounded-sw px-5 py-4']"
  >
    <div class="flex gap-3" :class="compact ? 'items-start' : 'items-center'">
      <span
        class="grid flex-none place-items-center rounded-full font-black"
        :class="[notice.iconClass, compact ? 'h-7 w-7 text-xs' : 'h-10 w-10 text-sm']"
      >
        {{ notice.icon }}
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-2">
          <h3 class="m-0 font-black text-[#18263c]" :class="compact ? 'text-sm' : 'text-base'">
            {{ notice.title }}
          </h3>
          <span
            v-if="displayLabel"
            class="rounded-full border bg-white px-2 py-0.5 text-xs font-bold"
            :class="notice.badgeClass"
          >
            {{ displayLabel }}
          </span>
        </div>
        <p
          class="mt-1 min-w-0 leading-[1.65] text-[#34516f]"
          :class="compact ? 'line-clamp-2 text-xs' : 'text-sm'"
        >
          {{ message }}
        </p>
        <p v-if="reviewerActionAt" class="mt-1 text-xs text-sw-muted">
          处理时间：{{ reviewerActionAt }}
        </p>
        <div v-if="$slots.actions" class="mt-3">
          <slot name="actions" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { HandlingStatus } from '@/types'
import { HANDLING_STATUS_LABELS } from '@/types'

interface Props {
  handlingStatus?: HandlingStatus
  handlingStatusLabel?: string | null
  reviewerRemark?: string | null
  reviewerActionAt?: string | null
  compact?: boolean
}

interface NoticeConfig {
  title: string
  fallbackMessage: string
  icon: string
  wrapperClass: string
  iconClass: string
  badgeClass: string
}

const props = withDefaults(defineProps<Props>(), {
  handlingStatus: null,
  handlingStatusLabel: '',
  reviewerRemark: '',
  reviewerActionAt: null,
  compact: false,
})

const noticeMap: Record<Exclude<HandlingStatus, null>, NoticeConfig> = {
  CORRECTION_REQUIRED: {
    title: '申请已退回补正',
    fallbackMessage: '请根据审核意见补充或更正材料，提交后会进入复审。',
    icon: '补',
    wrapperClass: 'border-[#f2c46d] bg-[#fffaf0]',
    iconClass: 'bg-[#fff1c4] text-[#9a6700]',
    badgeClass: 'border-[#f2c46d] text-[#9a6700]',
  },
  INITIAL_REVIEW_PASSED: {
    title: '申请已通过初审',
    fallbackMessage: '审核人员已完成处理，请留意后续办理通知。',
    icon: '过',
    wrapperClass: 'border-[#b7e4c7] bg-[#f4fbf7]',
    iconClass: 'bg-[#dcfce7] text-[#167044]',
    badgeClass: 'border-[#b7e4c7] text-[#167044]',
  },
  MANUAL_REVIEW_REQUIRED: {
    title: '已转人工复核',
    fallbackMessage: '审核人员已将该申请转入人工复核，请等待进一步处理。',
    icon: '复',
    wrapperClass: 'border-[#bfdbfe] bg-[#f3f8ff]',
    iconClass: 'bg-[#dbeafe] text-[#1d4ed8]',
    badgeClass: 'border-[#bfdbfe] text-[#1d4ed8]',
  },
}

const notice = computed(() => {
  if (!props.handlingStatus) return null
  return noticeMap[props.handlingStatus]
})

const displayLabel = computed(() => {
  if (!props.handlingStatus) return ''
  return props.handlingStatusLabel?.trim() || HANDLING_STATUS_LABELS[props.handlingStatus]
})

const message = computed(() => props.reviewerRemark?.trim() || notice.value?.fallbackMessage || '')
</script>
