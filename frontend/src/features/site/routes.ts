import type { RouteRecordRaw } from 'vue-router'

export const siteRoutes: RouteRecordRaw[] = [
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('./views/ProfileView.vue'),
    meta: { title: 'Profile' },
  },
  {
    path: '/structure',
    name: 'Structure',
    component: () => import('./views/StructureView.vue'),
    meta: { title: 'Structure' },
  },
  {
    path: '/facilities',
    name: 'Facilities',
    component: () => import('./views/FacilitiesView.vue'),
    meta: { title: 'Facilities' },
  },
  {
    path: '/ppdb',
    name: 'Ppdb',
    component: () => import('./views/PpdbView.vue'),
    meta: { title: 'Admission' },
  },
  {
    path: '/contact',
    name: 'Contact',
    component: () => import('./views/ContactView.vue'),
    meta: { title: 'Contact' },
  },
]
