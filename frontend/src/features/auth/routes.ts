import type { RouteRecordRaw } from 'vue-router'

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/LoginView.vue'),
    meta: {
      guestOnly: true,
      title: 'Sign in',
      description: 'Sign in to your account.',
    },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('./views/RegisterView.vue'),
    meta: {
      guestOnly: true,
      title: 'Create account',
      description: 'Create an account to get started.',
    },
  },
]
