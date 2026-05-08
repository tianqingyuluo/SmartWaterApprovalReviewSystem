import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'applicant',
      component: () => import('@/pages/ApplicantPage.vue'),
    },
    {
      path: '/review',
      name: 'reviewer',
      component: () => import('@/pages/ReviewerPage.vue'),
    },
  ],
})

export default router
