import type { RouteRecordRaw } from 'vue-router'

export const plansRoutes: RouteRecordRaw[] = [
  {
    path: 'plans',
    name: 'Plans',
    component: () => import('./views/PlansView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['superadmin'],
      title: 'Plans',
      description: 'Plan catalog: tiers, terms, prices, and defaults.',
    },
  },
]
