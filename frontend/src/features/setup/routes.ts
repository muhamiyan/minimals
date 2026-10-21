import type { RouteRecordRaw } from 'vue-router'

export const setupRoutes: RouteRecordRaw[] = [
  {
    path: '/setup',
    name: 'Setup',
    component: () => import('./views/SetupView.vue'),
    meta: {
      title: 'Setup',
      description:
        'First-run setup: connect a database, set your brand, and create the administrator.',
    },
  },
]
