import { watch } from 'vue'
import {
  createRouter,
  createWebHistory,
  type RouteLocationNormalized,
  type RouteRecordRaw,
} from 'vue-router'

import { i18n } from '@/app/i18n'
import AppShell from '@/app/AppShell.vue'
import { accountRoutes } from '@/features/account/routes'
import { activityAdminRoutes, activityRoutes } from '@/features/activity/routes'
import { authRoutes } from '@/features/auth/routes'
import { contactAdminRoutes } from '@/features/contact/routes'
import { useAuthStore } from '@/features/auth/store'
import { blogAdminRoutes, blogRoutes } from '@/features/blog/routes'
import { dashboardRoutes } from '@/features/dashboard/routes'
import { landingRoutes } from '@/features/landing/routes'
import { programAdminRoutes, programRoutes } from '@/features/program/routes'
import { scholarshipAdminRoutes, scholarshipRoutes } from '@/features/scholarship/routes'
import { setupRoutes } from '@/features/setup/routes'
import { siteRoutes } from '@/features/site/routes'
import { siteContentRoutes } from '@/features/site-content/routes'
import { brand } from '@/shared/brand'
import { authGuard } from './guard'

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...setupRoutes,
  ...landingRoutes,
  ...blogRoutes,
  ...activityRoutes,
  ...programRoutes,
  ...scholarshipRoutes,
  ...siteRoutes,
  ...siteContentRoutes,
  {
    path: '/dashboard',
    component: AppShell,
    children: [...dashboardRoutes, ...accountRoutes],
  },
  {
    path: '/blog',
    component: AppShell,
    children: [...blogAdminRoutes],
  },
  { path: '/admin/activities', redirect: '/activities/manage' },
  { path: '/admin/activities/new', redirect: '/activities/new' },
  {
    path: '/admin/activities/:slug/edit',
    redirect: (to) => `/activities/${String(to.params.slug)}/edit`,
  },
  {
    path: '/activities',
    component: AppShell,
    children: [...activityAdminRoutes],
  },
  { path: '/admin/programs', redirect: '/programs/manage' },
  { path: '/admin/programs/new', redirect: '/programs/new' },
  {
    path: '/admin/programs/:slug/edit',
    redirect: (to) => `/programs/${String(to.params.slug)}/edit`,
  },
  {
    path: '/programs',
    component: AppShell,
    children: [...programAdminRoutes],
  },
  {
    path: '/scholarships',
    component: AppShell,
    children: [...scholarshipAdminRoutes],
  },
  {
    path: '/messages',
    component: AppShell,
    children: [...contactAdminRoutes],
  },
  { path: '/admin', redirect: '/ppdb/manage' },
  { path: '/admin/blog', redirect: '/blog/manage' },
  { path: '/admin/blog/new', redirect: '/blog/new' },
  {
    path: '/admin/blog/:slug/edit',
    redirect: (to) => `/blog/${String(to.params.slug)}/edit`,
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(authGuard)

const { t, te } = i18n.global

function applyHead(to: RouteLocationNormalized) {
  const titleKey = `route.${String(to.name)}.title`
  const title = te(titleKey) ? t(titleKey) : to.meta.title
  document.title = title ? `${title} · ${brand.name}` : brand.name

  const descriptionKey = `route.${String(to.name)}.description`
  const description =
    (te(descriptionKey) ? t(descriptionKey) : to.meta.description) ||
    brand.description ||
    brand.tagline
  let meta = document.querySelector<HTMLMetaElement>('meta[name="description"]')
  if (description) {
    if (!meta) {
      meta = document.createElement('meta')
      meta.name = 'description'
      document.head.appendChild(meta)
    }
    meta.content = description
  } else {
    meta?.remove()
  }
}

router.afterEach((to) => applyHead(to))

watch(i18n.global.locale, () => applyHead(router.currentRoute.value))
window.addEventListener('brand:updated', () => applyHead(router.currentRoute.value))
window.addEventListener('site-content:updated', () =>
  applyHead(router.currentRoute.value),
)

window.addEventListener('auth:unauthorized', () => {
  const auth = useAuthStore()
  auth.user = null
  auth.checked = true
  const current = router.currentRoute.value
  if (current.matched.length > 0 && current.meta.requiresAuth) {
    router.replace({ path: '/login', query: { redirect: current.fullPath } })
  }
})

export default router
