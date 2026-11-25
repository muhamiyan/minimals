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
import { authRoutes } from '@/features/auth/routes'
import { useAuthStore } from '@/features/auth/store'
import { billingRoutes } from '@/features/billing/routes'
import { dashboardRoutes } from '@/features/dashboard/routes'
import { infraRoutes } from '@/features/infra/routes'
import { planRoutes } from '@/features/plan/routes'
import { plansRoutes } from '@/features/plans/routes'
import { setupRoutes } from '@/features/setup/routes'
import { tenancyRoutes } from '@/features/tenancy/routes'
import { todoRoutes } from '@/features/todo/routes'
import { brand } from '@/shared/brand'
import { authGuard } from './guard'

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...setupRoutes,
  {
    path: '/',
    component: AppShell,
    children: [
      ...dashboardRoutes,
      ...accountRoutes,
      ...tenancyRoutes,
      ...billingRoutes,
      ...todoRoutes,
      ...plansRoutes,
      ...planRoutes,
      ...infraRoutes,
    ],
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
