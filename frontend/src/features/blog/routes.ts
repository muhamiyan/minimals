import type { RouteRecordRaw } from 'vue-router'

export const blogRoutes: RouteRecordRaw[] = [
  {
    path: '/blog',
    name: 'BlogList',
    component: () => import('./views/BlogListView.vue'),
    meta: { title: 'Blog' },
  },
  {
    path: '/blog/:slug',
    name: 'BlogPost',
    component: () => import('./views/BlogPostView.vue'),
    meta: { title: 'Blog' },
  },
]

export const blogAdminRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'BlogAdminList',
    component: () => import('./views/BlogAdminListView.vue'),
    meta: { requiresAuth: true, adminOnly: true, title: 'Blog' },
  },
  {
    path: 'new',
    name: 'BlogAdminCreate',
    component: () => import('./views/BlogAdminEditView.vue'),
    meta: { requiresAuth: true, adminOnly: true, title: 'New post' },
  },
  {
    path: ':slug/edit',
    name: 'BlogAdminEdit',
    component: () => import('./views/BlogAdminEditView.vue'),
    meta: { requiresAuth: true, adminOnly: true, title: 'Edit post' },
  },
]
