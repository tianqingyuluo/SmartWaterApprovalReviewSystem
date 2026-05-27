import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentRole, isAuthenticated } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      meta: { title: '登录' },
      component: () => import('@/pages/LoginPage.vue'),
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'application-list',
          meta: { title: '申请列表' },
          component: () => import('@/pages/ApplicationListPage.vue'),
        },
        {
          path: '/apply',
          name: 'new-application',
          meta: { title: '新水务申请' },
          component: () => import('@/pages/NewApplicationPage.vue'),
        },
        {
          path: '/review',
          name: 'review-result',
          meta: { title: 'AI 智能审核结果' },
          component: () => import('@/pages/ReviewResultPage.vue'),
        },
        {
          path: '/knowledge-mcp',
          name: 'knowledge-mcp-demo',
          meta: { title: 'AI 知识库与 MCP 演示台' },
          component: () => import('@/pages/KnowledgeMcpDemoPage.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      meta: { title: '404' },
      component: () => import('@/pages/NotFoundPage.vue'),
    },
  ],
})

router.beforeEach((to) => {
  if (to.name === 'login') {
    if (isAuthenticated()) {
      return { path: '/' }
    }
    return true
  }

  if (!isAuthenticated()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  const role = getCurrentRole()
  if (!role) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (role === 'APPLICANT') {
    if (to.path === '/knowledge-mcp') {
      return { name: 'application-list' }
    }
    return true
  }

  if (role === 'REVIEWER') {
    if (to.path === '/apply') {
      return { name: 'application-list' }
    }
    if (to.path === '/knowledge-mcp') {
      return { name: 'review-result' }
    }
    return true
  }

  return true
})

export default router
