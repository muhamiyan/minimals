import type { RouteRecordRaw } from 'vue-router'

export const goakalRoutes: RouteRecordRaw[] = [
  {
    path: 'goakal',
    name: 'Goakal',
    component: () => import('./views/GoakalView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Goakal',
      description: 'Goakal payments and webhook secret.',
    },
  },
]
