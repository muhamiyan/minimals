import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'

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

  async function login(identifier: string, password: string): Promise<boolean> {
    error.value = ''
    try {
      const { data } = await api.post('/auth/login', { identifier, password })
      user.value = data
      checked.value = true
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, 'Login failed')
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
      error.value = getErrorMessage(e, 'Registration failed')
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

  return { user, checked, error, login, register, fetchMe, logout }
})
