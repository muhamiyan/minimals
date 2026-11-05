import type { RouteRecordRaw } from 'vue-router'

export const billingRoutes: RouteRecordRaw[] = [
  {
    path: 'billing',
    name: 'Billing',
    component: () => import('./views/BillingView.vue'),
    meta: {
      requiresAuth: true,
      ownerOnly: true,
      title: 'Billing',
      description: 'Invoices across organizations.',
    },
  },
]
