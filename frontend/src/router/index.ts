import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
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
          path: '/mcp-demo',
          name: 'mcp-demo',
          meta: { title: 'AI 知识库与 MCP 演示' },
          component: () => import('@/pages/McpDemoPage.vue'),
        },
      ],
    },
  ],
})

export default router
