import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import AppShell from '@/app/AppShell.vue'
import { authRoutes } from '@/features/auth/routes'
import { useAuthStore } from '@/features/auth/store'
import { blogAdminRoutes, blogRoutes } from '@/features/blog/routes'
import { dashboardRoutes } from '@/features/dashboard/routes'
import { landingRoutes } from '@/features/landing/routes'
import { setupRoutes } from '@/features/setup/routes'
import { authGuard } from './guard'

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  ...setupRoutes,
  ...landingRoutes,
  ...blogRoutes,
  {
    path: '/dashboard',
    component: AppShell,
    children: [...dashboardRoutes],
  },
  {
    path: '/admin/blog',
    component: AppShell,
    children: [...blogAdminRoutes],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(authGuard)

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
