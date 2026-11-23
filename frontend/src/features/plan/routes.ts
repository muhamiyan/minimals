import type { RouteRecordRaw } from 'vue-router'

export const planRoutes: RouteRecordRaw[] = [
  {
    path: 'plan',
    name: 'Plan',
    component: () => import('./views/PlanView.vue'),
    meta: {
      requiresAuth: true,
      ownerOnly: true,
      title: 'Plan',
      description: "Choose or switch the organization's plan.",
    },
  },
]
