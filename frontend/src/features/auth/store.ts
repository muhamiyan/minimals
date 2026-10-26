import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface AuthUser {
  id: string
  email: string
  username: string
  fullName: string
  appRole: string | null
  roles: string[]
  isActive: boolean
  createdOn: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const checked = ref(false)
  const error = ref('')
  const registrationMode = ref<'open' | 'closed' | null>(null)

  async function login(identifier: string, password: string): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post('/auth/login', { identifier, password })
      user.value = data
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.loginFailed'))
      return false
    }
  }

  async function register(payload: {
    fullName: string
    username: string
    email: string
    password: string
  }): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post('/auth/register', payload)
      user.value = data
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('auth.errors.registrationFailed'))
      return false
    }
  }

  async function fetchMe() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      user.value = null
    } finally {
      checked.value = true
    }
  }

  async function fetchRegistrationMode() {
    if (registrationMode.value !== null) return
    try {
      const { data } = await api.get('/auth/registration')
      registrationMode.value = data.mode === 'closed' ? 'closed' : 'open'
    } catch {
      // Fail open — matches the backend default; a blocked attempt still 403s.
      registrationMode.value = 'open'
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // Local session is cleared in finally even if the server call fails.
    } finally {
      user.value = null
      error.value = ''
    }
  }

  return {
    user,
    checked,
    error,
    registrationMode,
    login,
    register,
    fetchMe,
    fetchRegistrationMode,
    logout,
  }
})
