import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogList',
    component: () => import('./views/BlogListView.vue'),
  },
  {
    path: '/blog/:slug',
    name: 'BlogPost',
    component: () => import('./views/BlogPostView.vue'),
  },
]

export const blogAdminRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'BlogAdminList',
    component: () => import('./views/BlogAdminListView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: 'new',
    name: 'BlogAdminCreate',
    component: () => import('./views/BlogAdminEditView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: ':slug/edit',
    name: 'BlogAdminEdit',
    component: () => import('./views/BlogAdminEditView.vue'),
    meta: { requiresAuth: true, adminOnly: true },
  },
]
