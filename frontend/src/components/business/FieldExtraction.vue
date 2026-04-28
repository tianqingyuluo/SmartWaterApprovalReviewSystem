<template>
  <section class="card">
    <h2>字段抽取结果</h2>
    <table class="field-table">
      <thead>
        <tr>
          <th>字段</th>
          <th>值</th>
          <th>置信度</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(value, key) in fields" :key="key">
          <td class="field-name">{{ key }}</td>
          <td>{{ value || '—' }}</td>
          <td>
            <span
              v-if="confidence && confidence[key] !== undefined"
              class="conf-badge"
              :class="confClass(confidence[key])"
            >
              {{ (confidence[key] * 100).toFixed(0) }}%
            </span>
            <span v-else>—</span>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
interface Props {
  fields: Record<string, string>
  confidence: Record<string, number> | null
}

defineProps<Props>()

function confClass(val: number): string {
  if (val >= 0.8) return 'conf-high'
  if (val >= 0.5) return 'conf-mid'
  return 'conf-low'
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

.field-table {
  width: 100%;
  border-collapse: collapse;
}

.field-table th,
.field-table td {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.field-table th {
  background: #fafafa;
  font-weight: 600;
  color: #666;
}

.field-name {
  font-weight: 500;
  color: #333;
}

.conf-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.conf-high {
  background: #f6ffed;
  color: #52c41a;
}

.conf-mid {
  background: #fff7e6;
  color: #fa8c16;
}

.conf-low {
  background: #fff2f0;
  color: #ff4d4f;
}
</style>
