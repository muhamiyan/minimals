import type { RouteRecordRaw } from 'vue-router'

export const infraRoutes: RouteRecordRaw[] = [
  {
    path: 'infrastructure',
    name: 'Infrastructure',
    component: () => import('./views/DatabaseView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['superadmin'],
      title: 'Infrastructure',
      description: 'Active database engine and connection status.',
    },
  },
]
