import type { RouteRecordRaw } from 'vue-router'

export const activityRoutes: RouteRecordRaw[] = [
  {
    path: '/activities',
    name: 'ActivityList',
    component: () => import('./views/ActivityListView.vue'),
    meta: { title: 'Activities' },
  },
  {
    path: '/activities/:slug',
    name: 'ActivityPost',
    component: () => import('./views/ActivityPostView.vue'),
    meta: { title: 'Activities' },
  },
  {
    path: '/gallery',
    name: 'Gallery',
    component: () => import('./views/GalleryView.vue'),
    meta: { title: 'Gallery' },
  },
]

export const activityAdminRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'ActivityAdminList',
    component: () => import('./views/ActivityAdminListView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Activities' },
  },
  {
    path: 'new',
    name: 'ActivityAdminCreate',
    component: () => import('./views/ActivityAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'New activity' },
  },
  {
    path: ':slug/edit',
    name: 'ActivityAdminEdit',
    component: () => import('./views/ActivityAdminEditView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: 'Edit activity' },
  },
]
