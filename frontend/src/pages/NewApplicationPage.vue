<template>
  <div class="sw-page max-w-[1480px]">
    <h1 class="sw-page-title">新水务申请</h1>

    <form class="grid gap-[14px]" @submit.prevent="handleSubmit">
      <PageCard title="申请信息" subtitle="以下业务字段仅用于当前页面记录和展示，现有后端提交接口只接收三类材料附件。">
        <div class="grid gap-x-[34px] gap-y-[22px] max-[1080px]:grid-cols-2 max-md:grid-cols-1 [grid-template-columns:repeat(3,minmax(0,1fr))]">
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">申请类型 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <select v-model="form.applicationType" class="sw-select">
              <option value="新水务申请">新水务申请</option>
              <option value="用水变更申请">用水变更申请</option>
              <option value="报装申请">报装申请</option>
            </select>
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">申请人 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.applicantName" class="sw-input" placeholder="请输入申请人" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">联系电话 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.phone" class="sw-input" placeholder="请输入联系电话" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">申请单位 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.organization" class="sw-input" placeholder="请输入申请单位" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">所属部门</span>
            <input v-model="form.department" class="sw-input" placeholder="请输入所属部门" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">职务</span>
            <input v-model="form.position" class="sw-input" placeholder="请输入职务" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">用水项目名称 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.projectName" class="sw-input" placeholder="请输入用水项目名称" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">用水地址 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.address" class="sw-input" placeholder="请输入用水地址" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">用水用途 <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <select v-model="form.waterPurpose" class="sw-select">
              <option value="">请选择用水用途</option>
              <option value="生产用水">生产用水</option>
              <option value="生活用水">生活用水</option>
              <option value="农业灌溉">农业灌溉</option>
              <option value="工程建设">工程建设</option>
            </select>
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">计划用水量（m³/日） <small class="rounded-full bg-[#f3f8ff] px-[7px] py-0.5 text-xs font-semibold text-sw-muted">页面记录</small></span>
            <input v-model="form.dailyWaterUse" class="sw-input" placeholder="请输入计划用水量" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">计划用水时间</span>
            <input v-model="form.waterPeriod" class="sw-input" placeholder="例如：2026-06-01 至 2027-05-31" />
          </label>
          <label class="grid gap-2">
            <span class="flex items-center gap-2 font-extrabold text-[#26364f]">备注</span>
            <input v-model="form.remark" class="sw-input" placeholder="请输入备注信息（选填）" />
          </label>
        </div>
      </PageCard>

      <PageCard title="上传附件" subtitle="MVP 固定材料槽位：取水许可申请书、营业执照、身份证。允许缺失材料提交，但会产生部分结果或缺失材料提示。">
        <div class="mb-4 mt-[-4px] flex flex-wrap gap-3 text-[13px] text-sw-muted">
          <span class="rounded-full bg-[#f3f8ff] px-2.5 py-1.5">支持格式：jpg / jpeg / png / pdf / docx</span>
          <span class="rounded-full bg-[#f3f8ff] px-2.5 py-1.5">每类材料最多上传 1 个文件</span>
        </div>
        <div class="grid gap-[14px]">
          <FileUploadSlot
            v-for="slot in slots"
            :key="slot.type"
            :material-type="slot.type"
            :label="slot.label"
            :file="slot.file"
            :error="slot.error"
            :accept="acceptAttr"
            @change="(event) => onFileChange(event, slot.type)"
            @clear="clearSlot(slot.type)"
          />
        </div>
      </PageCard>

      <div v-if="submitError" class="sw-alert sw-alert-danger">{{ submitError }}</div>

      <div v-if="result" class="rounded-sw">
        <PageCard compact>
          <div class="grid items-center gap-5 max-[1080px]:grid-cols-2 max-md:grid-cols-1 [grid-template-columns:1fr_minmax(280px,0.7fr)_auto]">
            <div>
              <strong class="text-[17px] text-[#087443]">提交成功</strong>
              <p class="mt-2 leading-[1.7] text-sw-muted">后端已创建审核任务。可直接进入结果页查看当前任务状态。</p>
            </div>
            <dl class="m-0 grid [grid-template-columns:auto_1fr] gap-x-3 gap-y-2">
              <dt class="text-sw-muted">任务 ID</dt>
              <dd class="m-0"><code>{{ result.taskId }}</code></dd>
              <dt class="text-sw-muted">当前状态</dt>
              <dd class="m-0"><StatusTag :status="taskStatus" /></dd>
            </dl>
            <div class="flex justify-center gap-[18px] max-[1080px]:col-span-2 max-md:flex-col">
              <router-link class="sw-btn sw-btn-primary" :to="`/review?taskId=${result.taskId}`">
                查看 AI 初审结果
              </router-link>
              <button type="button" class="sw-btn sw-btn-ghost" @click="resetForm">继续新建</button>
            </div>
          </div>
        </PageCard>
      </div>

      <div v-if="isPolling && !isTerminalStatus" class="sw-alert sw-alert-info flex items-center gap-2.5">
        <span class="sw-spinner"></span>
        <span>AI 初审处理中，完成后可进入结果页查看材料状态、问题清单和审核意见草稿。</span>
      </div>

      <div v-if="showApplicantResult && taskData" class="sw-alert sw-alert-warning">
        预检查已生成：缺失材料 {{ taskData.missingMaterials.length }} 项，字段问题 {{ taskData.fieldIssues.length }} 项。完整问题清单请进入 AI 初审结果页查看。
      </div>

      <div v-if="taskStatus === 'FAILED'" class="sw-alert sw-alert-danger">
        当前任务暂无法生成结果，请检查材料文件是否可读，或重新提交新的任务。
      </div>

      <div class="flex justify-center gap-[18px] pt-3 max-md:flex-col">
        <button type="submit" class="sw-btn sw-btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交申请' }}
        </button>
        <button type="button" class="sw-btn sw-btn-ghost" @click="resetForm">重置</button>
      </div>
    </form>

    <p class="mt-5 text-center text-xs text-sw-faint">AI 仅提供审核辅助建议，最终审核结论以审批机关决定为准。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { appendMaterialFiles, getApplicantResult, getTaskStatus, submitTask, toApplicantResultView } from '@/api/task'
import { usePolling } from '@/composables/usePolling'
import type { ApplicantResultView, MaterialType, ProcessingStatus, SubmitResponse, TaskStatusResponse } from '@/types'
import { ACCEPTED_EXTENSIONS, MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'
import PageCard from '@/components/common/PageCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import FileUploadSlot from '@/components/business/FileUploadSlot.vue'

interface SlotState {
  type: MaterialType
  label: string
  file: File | null
  error: string
}

interface LocalApplicationForm {
  applicationType: string
  applicantName: string
  phone: string
  organization: string
  department: string
  position: string
  projectName: string
  address: string
  waterPurpose: string
  dailyWaterUse: string
  waterPeriod: string
  remark: string
}

const form = reactive<LocalApplicationForm>({
  applicationType: '新水务申请',
  applicantName: '',
  phone: '',
  organization: '',
  department: '',
  position: '',
  projectName: '',
  address: '',
  waterPurpose: '',
  dailyWaterUse: '',
  waterPeriod: '',
  remark: '',
})

const slots = reactive<SlotState[]>(
  MATERIAL_SLOTS.map((type) => ({ type, label: MATERIAL_LABELS[type], file: null, error: '' })),
)

const acceptAttr = ACCEPTED_EXTENSIONS.map((extension) => `.${extension}`).join(',')
const TERMINAL_STATUSES: ProcessingStatus[] = ['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED']

const submitting = ref(false)
const submitError = ref('')
const result = ref<SubmitResponse | null>(null)
const taskId = ref('')
const sessionId = ref<string | null>(null)
const taskStatus = ref<ProcessingStatus>('SUBMITTED')
const taskData = ref<ApplicantResultView | null>(null)
const polling = usePolling(
  () => getTaskStatus(taskId.value, sessionId.value).then((response) => response.data.data),
  3000,
  (statusResp: TaskStatusResponse) => TERMINAL_STATUSES.includes(statusResp.status),
  (statusResp: TaskStatusResponse) => {
    taskStatus.value = statusResp.status
    if (TERMINAL_STATUSES.includes(statusResp.status) && statusResp.status !== 'FAILED') {
      fetchApplicantResult()
    }
  },
)

const isTerminalStatus = computed(() => TERMINAL_STATUSES.includes(taskStatus.value))
const showApplicantResult = computed(() =>
  taskData.value !== null && (taskStatus.value === 'COMPLETED' || taskStatus.value === 'PARTIAL_SUCCESS'),
)

function onFileChange(event: Event, type: MaterialType) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  const slot = slots.find((candidate) => candidate.type === type)
  if (!slot) return

  slot.error = ''
  if (!file) {
    slot.file = null
    return
  }

  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  if (!ACCEPTED_EXTENSIONS.includes(extension)) {
    slot.error = '不支持的文件格式，请上传 jpg、jpeg、png、pdf 或 docx 文件。'
    slot.file = null
    input.value = ''
    return
  }

  slot.file = file
}

function clearSlot(type: MaterialType) {
  const slot = slots.find((candidate) => candidate.type === type)
  if (!slot) return

  slot.file = null
  slot.error = ''
  const input = document.getElementById(`file-${type}`) as HTMLInputElement | null
  if (input) input.value = ''
}

async function fetchApplicantResult() {
  try {
    const res = await getApplicantResult(taskId.value, sessionId.value)
    taskData.value = toApplicantResultView(res.data.data)
  } catch {
    taskData.value = null
  }
}

async function handleSubmit() {
  submitError.value = ''
  submitting.value = true

  try {
    const formData = new FormData()
    const selectedFiles = Object.fromEntries(slots.map((slot) => [slot.type, slot.file])) as Partial<Record<MaterialType, File | null>>
    appendMaterialFiles(formData, selectedFiles)

    const res = await submitTask(formData)
    const data = res.data.data
    result.value = data
    taskId.value = data.taskId
    sessionId.value = data.sessionId ?? null
    taskStatus.value = data.status ?? 'SUBMITTED'
    polling.start()
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : '提交失败，请重试。'
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.applicationType = '新水务申请'
  form.applicantName = ''
  form.phone = ''
  form.organization = ''
  form.department = ''
  form.position = ''
  form.projectName = ''
  form.address = ''
  form.waterPurpose = ''
  form.dailyWaterUse = ''
  form.waterPeriod = ''
  form.remark = ''

  slots.forEach((slot) => clearSlot(slot.type))
  polling.stop()
  result.value = null
  taskId.value = ''
  sessionId.value = null
  taskStatus.value = 'SUBMITTED'
  taskData.value = null
  submitError.value = ''
}

const isPolling = polling.isPolling
</script>
