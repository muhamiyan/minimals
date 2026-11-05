import type { RouteRecordRaw } from 'vue-router'

export const tenancyRoutes: RouteRecordRaw[] = [
  {
    // Pre-dashboard gate: a `user` with no organization must create one or
    // redeem an invite code. Rendered bare (no sidebar) via `fullscreen`.
    path: 'onboarding',
    name: 'Onboarding',
    component: () => import('./views/OnboardingView.vue'),
    meta: {
      requiresAuth: true,
      fullscreen: true,
      title: 'Set up your organization',
      description: 'Create an organization or redeem an invite code to continue.',
    },
  },
  {
    path: 'organizations',
    name: 'MyOrganizations',
    component: () => import('./views/MyOrganizationsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Organizations',
      description: 'Your organizations and invitations.',
    },
  },
  {
    path: 'organizations/:orgId',
    name: 'MyOrganization',
    component: () => import('./views/MyOrganizationView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Organization',
      description: 'Members, invite codes, and settings for one organization.',
    },
  },
  {
    path: 'tenancy',
    name: 'Tenancy',
    component: () => import('./views/OrganizationsView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['superadmin'],
      title: 'Tenancy console',
      description: 'Manage every organization on the platform.',
    },
  },
  {
    path: 'tenancy/:orgId',
    name: 'TenancyOrg',
    component: () => import('./views/OrganizationDetailView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['superadmin'],
      title: 'Organization',
      description: 'Members, subscription, and invite codes for one organization.',
    },
  },
]
