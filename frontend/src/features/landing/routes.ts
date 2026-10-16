import type { RouteRecordRaw } from 'vue-router'

export const landingRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('./views/LandingView.vue'),
  },
]
