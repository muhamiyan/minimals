import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface ContactMessage {
  id: string
  name: string
  phone: string
  email?: string
  message: string
  isRead: boolean
  createdOn?: string
}

interface ContactListResponse {
  items: ContactMessage[]
  total: number
  page: number
  perPage: number
}

export const useContactAdminStore = defineStore('contactAdmin', () => {
  const messages = ref<ContactMessage[]>([])
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(10)
  const loading = ref(false)
  const error = ref('')
  const checked = ref(false)

  async function fetchList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ContactListResponse>('/contact/admin/messages', {
        params: { page: nextPage, per_page: perPage.value },
      })
      messages.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('contactPage.errors.loadFailed'),
      )
      return false
    } finally {
      loading.value = false
      checked.value = true
    }
  }

  async function markRead(id: string, isRead: boolean): Promise<boolean> {
    error.value = ''
    try {
      await api.patch(`/contact/admin/messages/${id}`, { isRead })
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('contactPage.errors.updateFailed'))
      return false
    }
  }

  async function remove(id: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/contact/admin/messages/${id}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('contactPage.errors.deleteFailed'))
      return false
    }
  }

  return { messages, total, page, perPage, loading, error, checked, fetchList, markRead, remove }
})
