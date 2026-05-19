<template>
  <div class="min-h-screen px-4 py-8">
    <div class="mx-auto grid min-h-[calc(100vh-4rem)] max-w-[1120px] items-center gap-8 lg:grid-cols-[1.15fr_minmax(380px,420px)]">
      <section class="min-w-0">
        <p class="mb-3 text-sm font-bold uppercase tracking-[0.18em] text-sw-primary">SmartWater Approval Review System</p>
        <h1 class="text-[clamp(32px,4vw,56px)] font-black leading-[1.05] text-[#12213a]">
          审批辅助系统
        </h1>
        <p class="mt-5 max-w-[640px] text-base leading-[1.85] text-sw-muted">
          这是一个前端登录入口，用于进入申请、审核结果与知识库演示页面。当前版本不接真实账号体系，只做本地演示登录。
        </p>

        <div class="mt-8 grid gap-3 text-sm text-[#34516f] sm:grid-cols-2">
          <div class="rounded-[10px] border border-sw-line bg-white px-4 py-3">
            <strong class="block text-[#12213a]">申请处理</strong>
            <span>提交材料、查看状态、跟踪结果。</span>
          </div>
          <div class="rounded-[10px] border border-sw-line bg-white px-4 py-3">
            <strong class="block text-[#12213a]">知识库演示</strong>
            <span>检索知识条目，查看完整性检查。</span>
          </div>
        </div>
      </section>

      <section class="rounded-[16px] border border-sw-line bg-white p-6 shadow-[0_16px_40px_rgba(15,35,70,0.08)]">
        <h2 class="text-2xl font-black text-[#12213a]">登录</h2>
        <p class="mt-2 text-sm leading-[1.7] text-sw-muted">输入任意账号即可进入系统演示页。</p>

        <form class="mt-6 grid gap-4" @submit.prevent="handleLogin">
          <label class="grid gap-2">
            <span class="font-bold text-[#26364f]">用户名</span>
            <input v-model="username" class="sw-input" type="text" autocomplete="username" placeholder="请输入用户名" />
          </label>
          <label class="grid gap-2">
            <span class="font-bold text-[#26364f]">密码</span>
            <input v-model="password" class="sw-input" type="password" autocomplete="current-password" placeholder="请输入密码" />
          </label>

          <div v-if="errorMessage" class="sw-alert sw-alert-danger">
            {{ errorMessage }}
          </div>

          <button type="submit" class="sw-btn sw-btn-primary" :disabled="loading">
            {{ loading ? '登录中...' : '进入系统' }}
          </button>
        </form>

        <div class="mt-6 rounded-[10px] bg-[#f6f9fd] px-4 py-3 text-sm leading-[1.7] text-sw-muted">
          说明：登录状态仅保存在本地浏览器，不会请求后端认证接口。
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { setAuthToken } from '@/utils/auth'

const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    errorMessage.value = '请输入用户名和密码。'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    setAuthToken(`${username.value.trim()}-${Date.now()}`)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch {
    errorMessage.value = '登录失败，请重试。'
  } finally {
    loading.value = false
  }
}
</script>
