import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import AppShell from '@/app/AppShell.vue'
import { authRoutes } from '@/features/auth/routes'
import { useAuthStore } from '@/features/auth/store'
import { dashboardRoutes } from '@/features/dashboard/routes'
import { setupRoutes } from '@/features/setup/routes'
import { brand } from '@/shared/brand'
import { authGuard } from './guard'

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...setupRoutes,
  {
    path: '/',
    component: AppShell,
    children: [...dashboardRoutes],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(authGuard)

// Per-page <head>: title and meta description follow the matched route.
// Pages without meta.description fall back to the brand description that
// the server injected; when both are empty the tag is removed so a
// previous page's copy never lingers.
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · ${brand.name}` : brand.name

  const description = to.meta.description || brand.description
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
})

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
