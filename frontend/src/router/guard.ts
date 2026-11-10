import { useAuthStore } from '@/features/auth/store'
import { useSetupStore } from '@/features/setup/store'
import { useTenancyStore } from '@/features/tenancy/store'

/**
 * Owner-only routes (Billing): superadmin bypasses, everyone else must hold
 * `owner` in the active organization. A failed myOrgs lookup fails open —
 * the backend still enforces the real scope.
 */
async function enforceOwnerOnly(to: any): Promise<boolean | string> {
  if (!to.meta.ownerOnly) return true
  const auth = useAuthStore()
  if (auth.user?.appRole === 'superadmin') return true

  const tenancy = useTenancyStore()
  if (!tenancy.myOrgsLoaded && !tenancy.myOrgsError) {
    await tenancy.fetchMyOrgs()
  }
  if (tenancy.myOrgsError) return true
  return tenancy.currentOrg?.myRole === 'owner' ? true : '/'
}

/**
 * A plain `user` with no organization is routed to `/onboarding` before the
 * dashboard: they must create one or redeem an owner's invite code first.
 * `admin`/`superadmin` are never gated. If the lookup itself fails we fail
 * open — a network hiccup must not lock the user out of the app.
 */
async function enforceOnboarding(to: any): Promise<boolean | string> {
  const auth = useAuthStore()
  if (!auth.user || auth.user.appRole !== 'user') return true
  if (!to.meta.requiresAuth) return true

  const tenancy = useTenancyStore()
  // A failed lookup fails open but is not retried on every navigation —
  // DashboardView / OnboardingView refetch when they mount, so the gate
  // itself never hammers a struggling endpoint.
  if (!tenancy.myOrgsLoaded && !tenancy.myOrgsError) {
    await tenancy.fetchMyOrgs()
  }

  const onOnboarding = to.path === '/onboarding'
  if (tenancy.myOrgsError) return true // fail open
  const hasOrg = tenancy.myOrgs.length > 0
  if (onOnboarding) return hasOrg ? '/' : true
  return hasOrg ? true : '/onboarding'
}

export async function authGuard(to: any) {
  const setup = useSetupStore()
  if (setup.status === null && !setup.statusFailed) {
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
  if (to.meta.guestOnly) {
    if (auth.user) return '/'
    await auth.fetchRegistrationMode()
    if (to.name === 'Register' && auth.registrationMode === 'closed') {
      return { path: '/login' }
    }
  }
  if (to.meta.roles?.length && !to.meta.roles.includes(auth.user?.appRole ?? '')) {
    return '/'
  }
  const onboarding = await enforceOnboarding(to)
  if (onboarding !== true) return onboarding
  return enforceOwnerOnly(to)
}
