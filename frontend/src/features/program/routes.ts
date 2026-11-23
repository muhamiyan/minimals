import type { RouteRecordRaw } from 'vue-router'

export const programRoutes: RouteRecordRaw[] = [
  {
    path: '/programs',
    name: 'ProgramList',
    component: () => import('./views/ProgramListView.vue'),
    meta: { title: 'Programs' },
  },
  {
    path: '/programs/:slug',
    name: 'ProgramPost',
    component: () => import('./views/ProgramPostView.vue'),
    meta: { title: 'Programs' },
  },
]

export const programAdminRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'ProgramAdminList',
    component: () => import('./views/ProgramAdminListView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Programs' },
  },
  {
    path: 'new',
    name: 'ProgramAdminCreate',
    component: () => import('./views/ProgramAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'New program' },
  },
  {
    path: ':slug/edit',
    name: 'ProgramAdminEdit',
    component: () => import('./views/ProgramAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Edit program' },
  },
]
