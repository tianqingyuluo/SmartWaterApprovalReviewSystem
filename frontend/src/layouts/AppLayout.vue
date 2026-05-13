<template>
  <div class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <svg width="31" height="31" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 2.5C11.15 8.16 7.5 12.78 7.5 18.08C7.5 24.08 11.3 28 16 28C20.7 28 24.5 24.08 24.5 18.08C24.5 12.78 20.85 8.16 16 2.5Z" fill="white"/>
            <path d="M16 8.4C13.06 12.12 11.16 15.02 11.16 18.13C11.16 21.58 13.17 23.85 16 23.85C18.83 23.85 20.84 21.58 20.84 18.13C20.84 15.02 18.94 12.12 16 8.4Z" fill="#31a8ff"/>
          </svg>
        </div>
        <span>智慧水务管理平台</span>
      </div>

      <nav class="sidebar-nav" aria-label="主导航">
        <div class="nav-section-title">申请管理</div>
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
        >
          <span class="nav-icon" aria-hidden="true" v-html="item.icon"></span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-foot">MVP 演示环境</div>
    </aside>

    <div class="app-main-wrapper">
      <header class="app-header">
        <div class="breadcrumb">
          <span class="crumb-muted">申请管理</span>
          <span class="crumb-divider">/</span>
          <strong>{{ currentTitle }}</strong>
        </div>
        <div class="header-tools">
          <label class="toolbar-search">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
            <input disabled placeholder="按页面筛选区查询" />
          </label>
          <span class="tool-pill">无账号模式</span>
          <div class="user-chip" aria-label="当前演示用户">
            <span class="avatar">水</span>
            <span>张管理员</span>
          </div>
        </div>
      </header>

      <main class="app-main">
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

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 100;
  display: flex;
  width: 242px;
  flex-direction: column;
  background:
    radial-gradient(circle at 74% 6%, rgba(38, 142, 255, 0.34), transparent 28%),
    linear-gradient(180deg, var(--sw-sidebar) 0%, var(--sw-sidebar-deep) 100%);
  color: #eaf3ff;
  box-shadow: 12px 0 30px rgba(4, 26, 67, 0.18);
}

.brand {
  display: flex;
  min-height: 76px;
  align-items: center;
  gap: 12px;
  padding: 0 28px;
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
}

.sidebar-nav {
  flex: 1;
  padding: 22px 16px;
}

.nav-section-title {
  margin: 6px 14px 10px;
  color: rgba(234, 243, 255, 0.58);
  font-size: 12px;
  letter-spacing: 0.1em;
}

.nav-item {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 12px;
  margin: 6px 0;
  border-radius: 8px;
  padding: 0 16px;
  color: rgba(234, 243, 255, 0.84);
  font-weight: 700;
  text-decoration: none;
  transition: background 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.nav-item:hover,
.nav-item.active {
  background: linear-gradient(90deg, #1677ff 0%, #0f63df 100%);
  color: #fff;
  transform: translateX(2px);
}

.nav-icon {
  display: inline-flex;
}

.sidebar-foot {
  margin: 0 26px 24px;
  border-top: 1px solid rgba(234, 243, 255, 0.14);
  padding-top: 20px;
  color: rgba(234, 243, 255, 0.72);
  font-size: 13px;
}

.app-main-wrapper {
  min-width: 0;
  flex: 1;
  margin-left: 242px;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border-bottom: 1px solid rgba(213, 224, 236, 0.7);
  background: rgba(255, 255, 255, 0.92);
  padding: 0 32px;
  backdrop-filter: blur(14px);
  box-shadow: 0 8px 28px rgba(15, 35, 70, 0.05);
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #16233b;
  white-space: nowrap;
}

.crumb-muted,
.crumb-divider {
  color: var(--sw-muted);
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-search {
  display: flex;
  width: 238px;
  height: 36px;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--sw-line-strong);
  border-radius: 18px;
  background: #fff;
  color: #8a99ad;
  padding: 0 14px;
}

.toolbar-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  background: transparent;
  color: #8a99ad;
  outline: 0;
}

.tool-pill {
  border-radius: 16px;
  background: #eef6ff;
  color: #1763b8;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #334155;
  font-weight: 700;
}

.avatar {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #d9ebff, #fff);
  color: var(--sw-primary);
  box-shadow: inset 0 0 0 1px #cfe1f7;
}

.app-main {
  min-height: calc(100vh - 64px);
  padding: 28px 40px 38px;
}

@media (max-width: 980px) {
  .app-sidebar {
    position: static;
    width: 100%;
  }

  .app-shell {
    display: block;
  }

  .sidebar-nav {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 0 16px 16px;
  }

  .nav-section-title,
  .sidebar-foot {
    display: none;
  }

  .nav-item {
    min-width: max-content;
  }

  .app-main-wrapper {
    margin-left: 0;
  }

  .app-header {
    align-items: flex-start;
    flex-direction: column;
    padding: 14px 18px;
  }

  .header-tools {
    width: 100%;
    justify-content: space-between;
  }

  .toolbar-search {
    display: none;
  }

  .app-main {
    padding: 20px 16px 28px;
  }
}
</style>
