<template>
  <div class="min-h-screen max-[980px]:block min-[981px]:flex">
    <aside
      class="z-[100] flex w-full flex-col bg-[radial-gradient(circle_at_74%_6%,rgba(38,142,255,0.34),transparent_28%),linear-gradient(180deg,#06245a_0%,#041a43_100%)] text-[#eaf3ff] shadow-[12px_0_30px_rgba(4,26,67,0.18)] min-[981px]:fixed min-[981px]:inset-y-0 min-[981px]:left-0 min-[981px]:w-[242px]"
    >
      <div class="flex min-h-[76px] items-center gap-3 px-7 text-lg font-extrabold">
        <div class="grid h-[38px] w-[38px] place-items-center" aria-hidden="true">
          <svg width="31" height="31" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M16 2.5C11.15 8.16 7.5 12.78 7.5 18.08C7.5 24.08 11.3 28 16 28C20.7 28 24.5 24.08 24.5 18.08C24.5 12.78 20.85 8.16 16 2.5Z"
              fill="white"
            />
            <path
              d="M16 8.4C13.06 12.12 11.16 15.02 11.16 18.13C11.16 21.58 13.17 23.85 16 23.85C18.83 23.85 20.84 21.58 20.84 18.13C20.84 15.02 18.94 12.12 16 8.4Z"
              fill="#31a8ff"
            />
          </svg>
        </div>
        <span>智慧水务管理平台</span>
      </div>

      <nav
        class="flex-1 px-4 py-[22px] max-[980px]:flex max-[980px]:gap-2 max-[980px]:overflow-x-auto max-[980px]:px-4 max-[980px]:pb-4 max-[980px]:pt-0"
        aria-label="主导航"
      >
        <div class="mb-[10px] ml-[14px] mt-[6px] text-xs text-[rgba(234,243,255,0.58)] max-[980px]:hidden">
          申请管理
        </div>
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="my-1 flex min-h-11 items-center gap-3 rounded-lg px-4 font-bold no-underline transition-all duration-200 ease-out max-[980px]:min-w-max"
          :class="
            isActive(item.path)
              ? 'translate-x-0.5 bg-gradient-to-r from-sw-primary to-sw-primary-strong text-white'
              : 'text-[rgba(234,243,255,0.84)] hover:translate-x-0.5 hover:bg-gradient-to-r hover:from-sw-primary hover:to-sw-primary-strong hover:text-white'
          "
        >
          <span class="inline-flex" aria-hidden="true" v-html="item.icon"></span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div
        class="mx-[26px] mb-6 border-t border-[rgba(234,243,255,0.14)] pt-5 text-[13px] text-[rgba(234,243,255,0.72)] max-[980px]:hidden"
      >
        MVP 演示环境
      </div>
    </aside>

    <div class="min-w-0 flex-1 min-[981px]:ml-[242px]">
      <header
        class="sticky top-0 z-50 flex min-h-16 items-center justify-between gap-[18px] border-b border-[rgba(213,224,236,0.7)] bg-[rgba(255,255,255,0.92)] px-8 shadow-[0_8px_28px_rgba(15,35,70,0.05)] backdrop-blur-[14px] max-[980px]:flex-col max-[980px]:items-start max-[980px]:px-[18px] max-[980px]:py-[14px]"
      >
        <div class="flex items-center gap-[10px] whitespace-nowrap text-[#16233b]">
          <span class="text-sw-muted">申请管理</span>
          <span class="text-sw-muted">/</span>
          <strong>{{ currentTitle }}</strong>
        </div>
        <div class="flex items-center gap-4 max-[980px]:w-full max-[980px]:justify-between">
          <label
            class="flex h-9 w-[238px] items-center gap-2 rounded-[18px] border border-sw-line-strong bg-white px-[14px] text-[#8a99ad] max-[980px]:hidden"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input class="min-w-0 flex-1 border-0 bg-transparent text-[#8a99ad] outline-0" disabled placeholder="按页面筛选区查询" />
          </label>
          <span class="rounded-2xl bg-[#eef6ff] px-3 py-1.5 text-xs font-bold text-[#1763b8]">无账号模式</span>
          <div class="flex items-center gap-[9px] font-bold text-slate-700" aria-label="当前演示用户">
            <span class="grid h-8 w-8 place-items-center rounded-full bg-[linear-gradient(135deg,#d9ebff,#fff)] text-sw-primary shadow-[inset_0_0_0_1px_#cfe1f7]">水</span>
            <span>张管理员</span>
          </div>
        </div>
      </header>

      <main class="min-h-[calc(100vh-64px)] px-10 pb-[38px] pt-7 max-[980px]:px-4 max-[980px]:pb-7 max-[980px]:pt-5">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const menuItems = [
  {
    path: '/',
    label: '申请列表',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg>',
  },
  {
    path: '/apply',
    label: '新水务申请',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="M9 15h6"/></svg>',
  },
  {
    path: '/review',
    label: 'AI 初审结果',
    icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  },
]

const currentTitle = computed(() => route.meta.title?.toString() || '申请列表')

function isActive(path: string) {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>
