import { useAuthStore } from '@/features/auth/store'
import { useSetupStore } from '@/features/setup/store'

export async function authGuard(to: any) {
  const setup = useSetupStore()
  if (setup.status === null) {
    await setup.fetchStatus()
  }
  if (setup.status?.setupRequired) {
    return to.path === '/setup' ? true : '/setup'
  }
  if (to.path === '/setup') {
    return '/'
  }

  const auth = useAuthStore()
  if (!auth.checked) {
    await auth.fetchMe()
  }
  if (to.meta.requiresAuth && !auth.user) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.user) {
    return '/'
  }
  return true
}
