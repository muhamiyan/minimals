import type { RouteRecordRaw } from 'vue-router'

export const contactAdminRoutes: RouteRecordRaw[] = [
  {
    path: 'manage',
    name: 'ContactAdminList',
    component: () => import('./views/ContactAdminListView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Messages' },
  },
]
