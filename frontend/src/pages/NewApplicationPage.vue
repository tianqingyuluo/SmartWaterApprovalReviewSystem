<template>
  <div class="sw-page new-application-page">
    <h1 class="sw-page-title">新水务申请</h1>

    <form class="application-form" @submit.prevent="handleSubmit">
      <PageCard title="申请信息" subtitle="以下业务字段仅用于当前页面记录和展示，现有后端提交接口只接收三类材料附件。">
        <div class="form-grid">
          <label class="form-field">
            <span>申请类型 <small>页面记录</small></span>
            <select v-model="form.applicationType" class="sw-select">
              <option value="新水务申请">新水务申请</option>
              <option value="用水变更申请">用水变更申请</option>
              <option value="报装申请">报装申请</option>
            </select>
          </label>
          <label class="form-field">
            <span>申请人 <small>页面记录</small></span>
            <input v-model="form.applicantName" class="sw-input" placeholder="请输入申请人" />
          </label>
          <label class="form-field">
            <span>联系电话 <small>页面记录</small></span>
            <input v-model="form.phone" class="sw-input" placeholder="请输入联系电话" />
          </label>
          <label class="form-field">
            <span>申请单位 <small>页面记录</small></span>
            <input v-model="form.organization" class="sw-input" placeholder="请输入申请单位" />
          </label>
          <label class="form-field">
            <span>所属部门</span>
            <input v-model="form.department" class="sw-input" placeholder="请输入所属部门" />
          </label>
          <label class="form-field">
            <span>职务</span>
            <input v-model="form.position" class="sw-input" placeholder="请输入职务" />
          </label>
          <label class="form-field">
            <span>用水项目名称 <small>页面记录</small></span>
            <input v-model="form.projectName" class="sw-input" placeholder="请输入用水项目名称" />
          </label>
          <label class="form-field">
            <span>用水地址 <small>页面记录</small></span>
            <input v-model="form.address" class="sw-input" placeholder="请输入用水地址" />
          </label>
          <label class="form-field">
            <span>用水用途 <small>页面记录</small></span>
            <select v-model="form.waterPurpose" class="sw-select">
              <option value="">请选择用水用途</option>
              <option value="生产用水">生产用水</option>
              <option value="生活用水">生活用水</option>
              <option value="农业灌溉">农业灌溉</option>
              <option value="工程建设">工程建设</option>
            </select>
          </label>
          <label class="form-field">
            <span>计划用水量（m³/日） <small>页面记录</small></span>
            <input v-model="form.dailyWaterUse" class="sw-input" placeholder="请输入计划用水量" />
          </label>
          <label class="form-field">
            <span>计划用水时间</span>
            <input v-model="form.waterPeriod" class="sw-input" placeholder="例如：2026-06-01 至 2027-05-31" />
          </label>
          <label class="form-field">
            <span>备注</span>
            <input v-model="form.remark" class="sw-input" placeholder="请输入备注信息（选填）" />
          </label>
        </div>
      </PageCard>

      <PageCard title="上传附件" subtitle="MVP 固定材料槽位：取水许可申请书、营业执照、身份证。允许缺失材料提交，但会产生部分结果或缺失材料提示。">
        <div class="support-line">
          <span>支持格式：jpg / jpeg / png / pdf</span>
          <span>每类材料最多上传 1 个文件</span>
        </div>
        <div class="upload-grid">
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

      <div v-if="result" class="submit-result">
        <PageCard compact>
          <div class="result-grid">
            <div>
              <strong>提交成功</strong>
              <p>后端已创建审核任务，请保存任务 ID 和会话 ID。MVP 无账号模式下，结果页需要这两个标识访问。</p>
            </div>
            <dl>
              <dt>任务 ID</dt>
              <dd><code>{{ result.taskId }}</code></dd>
              <dt>会话 ID</dt>
              <dd><code>{{ result.sessionId }}</code></dd>
              <dt>当前状态</dt>
              <dd><StatusTag :status="taskStatus" /></dd>
            </dl>
            <div class="result-actions">
              <router-link class="sw-btn sw-btn-primary" :to="`/review?taskId=${result.taskId}&sessionId=${result.sessionId}`">
                查看 AI 初审结果
              </router-link>
              <button type="button" class="sw-btn sw-btn-ghost" @click="resetForm">继续新建</button>
            </div>
          </div>
        </PageCard>
      </div>

      <div v-if="isPolling && !isTerminalStatus" class="sw-alert sw-alert-info polling-line">
        <span class="sw-spinner"></span>
        <span>AI 初审处理中，完成后可进入结果页查看材料状态、问题清单和审核意见草稿。</span>
      </div>

      <div v-if="showApplicantResult && taskData" class="sw-alert sw-alert-warning">
        预检查已生成：缺失材料 {{ taskData.missingMaterials.length }} 项，字段问题 {{ taskData.fieldIssues.length }} 项。完整问题清单请进入 AI 初审结果页查看。
      </div>

      <div v-if="taskStatus === 'FAILED'" class="sw-alert sw-alert-danger">
        当前任务暂无法生成结果，请检查材料文件是否可读，或重新提交新的任务。
      </div>

      <div class="form-actions">
        <button type="submit" class="sw-btn sw-btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交申请' }}
        </button>
        <button type="button" class="sw-btn sw-btn-ghost" @click="resetForm">重置</button>
      </div>
    </form>

    <p class="disclaimer">AI 仅提供审核辅助建议，最终审核结论以审批机关决定为准。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { getApplicantResult, getTaskStatus, submitTask, toApplicantResultView } from '@/api/task'
import { usePolling } from '@/composables/usePolling'
import type { ApplicantResultView, MaterialType, ProcessingStatus, SubmitResponse, TaskStatusResponse } from '@/types'
import { ACCEPTED_EXTENSIONS, MATERIAL_FORM_FIELDS, MATERIAL_LABELS, MATERIAL_SLOTS } from '@/types'
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
const sessionId = ref('')
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
    slot.error = '不支持的文件格式，请上传 jpg、jpeg、png 或 pdf 文件。'
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
    slots.forEach((slot) => {
      if (slot.file) {
        formData.append(MATERIAL_FORM_FIELDS[slot.type], slot.file)
      }
    })

    const res = await submitTask(formData)
    const data = res.data.data
    result.value = data
    taskId.value = data.taskId
    sessionId.value = data.sessionId
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
  sessionId.value = ''
  taskStatus.value = 'SUBMITTED'
  taskData.value = null
  submitError.value = ''
}

const isPolling = polling.isPolling
</script>

<style scoped>
.new-application-page {
  max-width: 1480px;
}

.application-form {
  display: grid;
  gap: 14px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px 34px;
}

.form-field {
  display: grid;
  gap: 8px;
}

.form-field span {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #26364f;
  font-weight: 800;
}

.form-field small {
  border-radius: 999px;
  background: #f3f8ff;
  color: var(--sw-muted);
  padding: 2px 7px;
  font-size: 12px;
  font-weight: 600;
}

.support-line {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: -4px 0 16px;
  color: var(--sw-muted);
  font-size: 13px;
}

.support-line span {
  border-radius: 999px;
  background: #f3f8ff;
  padding: 6px 10px;
}

.upload-grid {
  display: grid;
  gap: 14px;
}

.submit-result {
  border-radius: var(--sw-radius);
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr minmax(280px, 0.7fr) auto;
  align-items: center;
  gap: 20px;
}

.result-grid strong {
  color: #087443;
  font-size: 17px;
}

.result-grid p {
  margin-top: 8px;
  color: var(--sw-muted);
  line-height: 1.7;
}

.result-grid dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px 12px;
  margin: 0;
}

.result-grid dt {
  color: var(--sw-muted);
}

.result-grid dd {
  margin: 0;
}

.result-actions,
.form-actions {
  display: flex;
  justify-content: center;
  gap: 18px;
}

.form-actions {
  padding: 12px 0 0;
}

.polling-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.disclaimer {
  margin-top: 20px;
  color: var(--sw-faint);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 1080px) {
  .form-grid,
  .result-grid {
    grid-template-columns: 1fr 1fr;
  }

  .result-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .form-grid,
  .result-grid {
    grid-template-columns: 1fr;
  }

  .result-actions,
  .form-actions {
    flex-direction: column;
  }
}
</style>
