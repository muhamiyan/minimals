import type { RouteRecordRaw } from 'vue-router'

import AppShell from '@/app/AppShell.vue'

import { SITE_SECTIONS } from './sections'

const PATHS: Record<string, string> = {
  ppdb: '/ppdb/manage',
  contact: '/contact/manage',
}

export const siteContentRoutes: RouteRecordRaw[] = SITE_SECTIONS.map((section) => ({
  path: PATHS[section.key] as string,
  component: AppShell,
  children: [
    {
      path: '',
      name: section.routeName,
      component: () => import('./views/SiteContentView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true, title: 'Site content' },
    },
  ],
}))
