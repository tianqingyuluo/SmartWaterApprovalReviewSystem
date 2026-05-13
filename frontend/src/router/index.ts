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
          component: () => import('@/pages/ApplicationListPage.vue'),
        },
        {
          path: '/apply',
          name: 'new-application',
          component: () => import('@/pages/NewApplicationPage.vue'),
        },
        {
          path: '/review',
          name: 'review-result',
          component: () => import('@/pages/ReviewResultPage.vue'),
        },
      ],
    },
  ],
})

export default router
