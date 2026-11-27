import type { RouteRecordRaw } from 'vue-router'

export const scholarshipRoutes: RouteRecordRaw[] = [
  {
    path: '/scholarships',
    name: 'ScholarshipList',
    component: () => import('./views/ScholarshipListView.vue'),
    meta: { title: 'Scholarships' },
  },
  {
    path: '/scholarships/:slug',
    name: 'ScholarshipPost',
    component: () => import('./views/ScholarshipPostView.vue'),
    meta: { title: 'Scholarships' },
  },
]

export const scholarshipAdminRoutes: RouteRecordRaw[] = [
  {
    path: 'manage',
    name: 'ScholarshipAdminList',
    component: () => import('./views/ScholarshipAdminListView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Scholarships' },
  },
  {
    path: 'new',
    name: 'ScholarshipAdminCreate',
    component: () => import('./views/ScholarshipAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'New scholarship' },
  },
  {
    path: ':slug/edit',
    name: 'ScholarshipAdminEdit',
    component: () => import('./views/ScholarshipAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Edit scholarship' },
  },
]
