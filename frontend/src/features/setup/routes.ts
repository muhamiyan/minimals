import type { RouteRecordRaw } from 'vue-router'

export const setupRoutes: RouteRecordRaw[] = [
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('./views/SetupView.vue'),
  },
]
