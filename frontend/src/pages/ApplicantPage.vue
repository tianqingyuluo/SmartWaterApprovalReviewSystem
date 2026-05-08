<template>
  <div class="applicant-page">
    <header class="page-header">
      <h1>取水许可智能审核 — 材料提交</h1>
      <p class="page-desc">请按材料类型上传文件。部分材料缺失时仍可提交，系统将提示缺失项。</p>
    </header>

    <form class="upload-form" @submit.prevent="handleSubmit">
      <div
        v-for="slot in slots"
        :key="slot.type"
        class="upload-slot"
      >
        <div class="slot-header">
          <label class="slot-label">{{ slot.label }}</label>
          <span class="slot-required">(建议上传)</span>
        </div>

        <div class="slot-body">
          <div v-if="slot.file" class="file-preview">
            <span class="file-name">{{ slot.file.name }}</span>
            <span class="file-size">{{ formatSize(slot.file.size) }}</span>
            <button type="button" class="btn-clear" @click="clearSlot(slot.type)">移除</button>
          </div>
          <div v-else class="file-upload-box">
            <input
              :id="'file-' + slot.type"
              type="file"
              :accept="acceptAttr"
              class="file-input"
              @change="(e) => onFileChange(e, slot.type)"
            />
            <label :for="'file-' + slot.type" class="file-label">
              <span class="upload-icon">+</span>
              <span>点击上传</span>
            </label>
          </div>
        </div>

        <p class="slot-hint">支持 jpg、jpeg、png、pdf 格式。完整版后续支持 Word 文件。</p>
        <p v-if="slot.error" class="slot-error">{{ slot.error }}</p>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn-submit" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交材料' }}
        </button>
      </div>
    </form>

    <p v-if="submitError" class="submit-error">{{ submitError }}</p>

    <div v-if="result" class="result-section">
      <div class="result-card">
        <h2>提交成功</h2>
        <dl>
          <dt>任务 ID</dt>
          <dd><code>{{ result.taskId }}</code></dd>
          <dt>会话 ID</dt>
          <dd><code>{{ result.sessionId }}</code></dd>
        </dl>
        <p class="result-note">请保存以上 ID，用于后续查询审核结果。</p>
        <button class="btn-new" @click="resetForm">提交新的材料</button>
      </div>
    </div>

    <div v-if="isPolling && !isTerminalStatus" class="polling-section">
      <StatusBadge :status="taskStatus" audience="applicant" />
      <p class="polling-hint">审核处理中，请稍候...</p>
    </div>

    <div v-if="showApplicantResult && taskData" class="applicant-result">
      <h2>预检查结果</h2>

      <div v-if="taskData.missingMaterials?.length" class="app-result-card missing">
        <h3>缺失材料</h3>
        <ul>
          <li v-for="m in taskData.missingMaterials" :key="m">
            {{ MATERIAL_LABELS[m as MaterialType] || m }}
          </li>
        </ul>
      </div>

      <div v-if="taskData.fieldIssues?.length" class="app-result-card issues">
        <h3>字段问题</h3>
        <div v-for="(issue, idx) in taskData.fieldIssues" :key="idx" class="issue-item">
          <span class="issue-severity" :class="'sev-' + issue.severity.toLowerCase()">
            {{ severityLabel(issue.severity) }}
          </span>
          {{ issue.description }}
        </div>
      </div>

      <div v-if="taskData.suggestions?.length" class="app-result-card suggestions">
        <h3>建议</h3>
        <ul>
          <li v-for="(s, idx) in taskData.suggestions" :key="idx">{{ s }}</li>
        </ul>
      </div>

      <div class="app-result-actions">
        <button class="btn-new" @click="resetForm">提交新的材料</button>
      </div>
    </div>

    <div v-if="taskStatus === 'FAILED'" class="applicant-result">
      <h2>预检查结果</h2>
      <div class="app-result-card issues">
        <h3>暂无法生成结果</h3>
        <p>请检查材料文件是否可读，或重新提交新的任务。</p>
      </div>
      <div class="app-result-actions">
        <button class="btn-new" @click="resetForm">提交新的材料</button>
      </div>
    </div>

    <p class="disclaimer">本系统提供 AI 辅助审核建议，最终审核结果以审批机关决定为准。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import {
  submitTask,
  getTaskStatus,
  getApplicantResult,
  toApplicantResultView,
} from '@/api/task'
import { usePolling } from '@/composables/usePolling'
import type { SubmitResponse, MaterialType, Severity, TaskStatusResponse, ApplicantResultView } from '@/types'
import {
  MATERIAL_SLOTS,
  MATERIAL_LABELS,
  ACCEPTED_EXTENSIONS,
  MATERIAL_FORM_FIELDS,
} from '@/types'
import type { ProcessingStatus } from '@/types'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface SlotState {
  type: string
  label: string
  file: File | null
  error: string
}

const slots = reactive<SlotState[]>(
  MATERIAL_SLOTS.map((t) => ({ type: t, label: MATERIAL_LABELS[t], file: null, error: '' })),
)

const acceptAttr = ACCEPTED_EXTENSIONS.map((e) => `.${e}`).join(',')

const submitting = ref(false)
const submitError = ref('')
const result = ref<SubmitResponse | null>(null)
const taskId = ref('')
const sessionId = ref('')
const isPolling = ref(false)
const taskStatus = ref<ProcessingStatus>('SUBMITTED')
const taskData = ref<ApplicantResultView | null>(null)

const TERMINAL_STATUSES: ProcessingStatus[] = ['COMPLETED', 'PARTIAL_SUCCESS', 'FAILED']

const showApplicantResult = computed(() =>
  taskData.value !== null &&
  (taskStatus.value === 'COMPLETED' || taskStatus.value === 'PARTIAL_SUCCESS'),
)

const isTerminalStatus = computed(() => TERMINAL_STATUSES.includes(taskStatus.value))

function severityLabel(severity: Severity): string {
  if (severity === 'BLOCKER') return '阻断'
  if (severity === 'WARNING') return '警告'
  return '提示'
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function onFileChange(event: Event, type: string) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const slot = slots.find((s) => s.type === type)!
  slot.error = ''

  if (!file) {
    slot.file = null
    return
  }

  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    slot.error = '不支持的文件格式，请上传 jpg、jpeg、png 或 pdf 文件'
    input.value = ''
    return
  }

  slot.file = file
}

function clearSlot(type: string) {
  const slot = slots.find((s) => s.type === type)!
  slot.file = null
  slot.error = ''
  const input = document.getElementById(`file-${type}`) as HTMLInputElement
  if (input) input.value = ''
}

async function fetchApplicantResult() {
  try {
    const res = await getApplicantResult(taskId.value, sessionId.value)
    taskData.value = toApplicantResultView(res.data.data)
  } catch {
    // result fetch failure is non-blocking; polling already updated status
  }
}

async function handleSubmit() {
  submitError.value = ''

  submitting.value = true
  try {
    const formData = new FormData()
    slots.forEach((s) => {
      if (s.file) {
        formData.append(MATERIAL_FORM_FIELDS[s.type as MaterialType], s.file)
      }
    })

    const res = await submitTask(formData)
    const data = res.data.data
    result.value = data
    taskId.value = data.taskId
    sessionId.value = data.sessionId
    isPolling.value = true

    const { start } = usePolling(
      () => getTaskStatus(data.taskId, data.sessionId).then((r) => r.data.data),
      3000,
      (statusResp: TaskStatusResponse) => TERMINAL_STATUSES.includes(statusResp.status),
      (statusResp: TaskStatusResponse) => {
        taskStatus.value = statusResp.status
        if (TERMINAL_STATUSES.includes(statusResp.status)) {
          if (statusResp.status !== 'FAILED') {
            fetchApplicantResult()
          }
        }
      },
    )
    start()
  } catch (e) {
    submitError.value = e instanceof Error ? e.message : '提交失败，请重试'
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  slots.forEach((s) => {
    s.file = null
    s.error = ''
    const input = document.getElementById(`file-${s.type}`) as HTMLInputElement
    if (input) input.value = ''
  })
  result.value = null
  taskId.value = ''
  sessionId.value = ''
  isPolling.value = false
  taskStatus.value = 'SUBMITTED'
  taskData.value = null
  submitError.value = ''
}
</script>

<style scoped>
.applicant-page {
  max-width: 680px;
  margin: 0 auto;
  padding: 32px 16px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 24px;
  margin-bottom: 8px;
}

.page-desc {
  color: #666;
  font-size: 14px;
}

.upload-slot {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.slot-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.slot-label {
  font-weight: 600;
  font-size: 16px;
}

.slot-required {
  font-size: 12px;
  color: #999;
}

.file-upload-box {
  text-align: center;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.file-label {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 24px 48px;
  border: 2px dashed #ccc;
  border-radius: 8px;
  cursor: pointer;
  color: #666;
  transition: border-color 0.2s;
}

.file-label:hover {
  border-color: #1890ff;
}

.upload-icon {
  font-size: 28px;
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #999;
  font-size: 12px;
}

.btn-clear {
  border: none;
  background: none;
  color: #ff4d4f;
  cursor: pointer;
  font-size: 13px;
}

.slot-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.slot-error {
  margin-top: 4px;
  font-size: 13px;
  color: #ff4d4f;
}

.form-actions {
  text-align: center;
  margin-top: 24px;
}

.btn-submit {
  padding: 12px 48px;
  font-size: 16px;
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-submit:hover {
  background: #40a9ff;
}

.btn-submit:disabled {
  background: #91d5ff;
  cursor: not-allowed;
}

.submit-error {
  text-align: center;
  color: #ff4d4f;
  margin-top: 16px;
}

.result-section {
  margin-top: 32px;
}

.result-card {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  padding: 24px;
}

.result-card h2 {
  font-size: 18px;
  color: #52c41a;
  margin-bottom: 16px;
}

.result-card dl {
  margin-bottom: 16px;
}

.result-card dt {
  font-size: 13px;
  color: #666;
}

.result-card dd {
  margin-left: 0;
  margin-bottom: 8px;
}

.result-card code {
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 13px;
}

.result-note {
  font-size: 14px;
  color: #333;
  margin-bottom: 16px;
}

.btn-new {
  border: 1px solid #d9d9d9;
  background: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.polling-section {
  margin-top: 24px;
  text-align: center;
}

.polling-hint {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.applicant-result {
  margin-top: 32px;
}

.applicant-result h2 {
  font-size: 18px;
  margin-bottom: 16px;
}

.app-result-card {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.app-result-card h3 {
  font-size: 15px;
  margin-bottom: 8px;
}

.app-result-card.missing {
  background: #fff7e6;
  border: 1px solid #ffd591;
}

.app-result-card.missing h3 {
  color: #fa8c16;
}

.app-result-card.issues {
  background: #fff2f0;
  border: 1px solid #ffccc7;
}

.app-result-card.issues h3 {
  color: #ff4d4f;
}

.app-result-card.suggestions {
  background: #e6f7ff;
  border: 1px solid #91d5ff;
}

.app-result-card.suggestions h3 {
  color: #1890ff;
}

.app-result-card ul {
  list-style: disc;
  padding-left: 20px;
}

.app-result-card li {
  font-size: 14px;
  margin-bottom: 4px;
}

.issue-item {
  font-size: 14px;
  margin-bottom: 6px;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.issue-severity {
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.sev-blocker {
  background: #ff4d4f;
  color: #fff;
}

.sev-warning {
  background: #fa8c16;
  color: #fff;
}

.sev-info {
  background: #ddd;
  color: #666;
}

.app-result-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.disclaimer {
  margin-top: 48px;
  text-align: center;
  font-size: 12px;
  color: #bbb;
}
</style>
