import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface GoakalTransaction {
  id: string
  externalId: string
  paymentId?: string | null
  status: string
  amount?: number | null
  email?: string | null
  phone?: string | null
  name?: string | null
  /** Absent until the transaction is linked (exclude_none). */
  invoiceId?: string | null
  createdOn?: string | null
  paidOn?: string | null
}

export interface GoakalSettings {
  configured: boolean
}

interface Paged<T> {
  items: T[]
  total: number
  page: number
  perPage: number
}

export const useGoakalStore = defineStore('goakal', () => {
  const items = ref<GoakalTransaction[]>([])
  const total = ref(0)
  const page = ref(1)
  const listLoading = ref(false)
  const listError = ref('')
  let listSeq = 0

  const settingsLoading = ref(false)
  const settings = ref<GoakalSettings | null>(null)
  const settingsError = ref('')
  const settingsSaving = ref(false)
  const settingsSaveError = ref('')

  const linkError = ref('')
  const linkingId = ref<string | null>(null)

  async function fetchList(query: { search: string; perPage: number }): Promise<void> {
    const seq = ++listSeq
    listLoading.value = true
    listError.value = ''
    try {
      const { data } = await api.get<Paged<GoakalTransaction>>('/goakal/transactions', {
        params: {
          search: query.search.trim() || undefined,
          page: page.value,
          per_page: query.perPage,
        },
      })
      if (seq !== listSeq) return
      items.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? page.value
    } catch (e: any) {
      if (seq !== listSeq) return
      listError.value = getErrorMessage(e, i18n.global.t('goakal.errors.load'))
      items.value = []
      total.value = 0
    } finally {
      if (seq === listSeq) listLoading.value = false
    }
  }

  function setPage(next: number): void {
    page.value = next
  }

  async function fetchSettings(): Promise<void> {
    settingsLoading.value = true
    settingsError.value = ''
    try {
      const { data } = await api.get<GoakalSettings>('/goakal/settings')
      settings.value = data
    } catch (e: any) {
      settingsError.value = getErrorMessage(e, i18n.global.t('goakal.errors.settings'))
    } finally {
      settingsLoading.value = false
    }
  }

  async function saveSettings(secret: string): Promise<boolean> {
    settingsSaveError.value = ''
    settingsSaving.value = true
    try {
      const { data } = await api.put<GoakalSettings>('/goakal/settings', { secret })
      settings.value = data
      return true
    } catch (e: any) {
      settingsSaveError.value = getErrorMessage(e, i18n.global.t('goakal.errors.saveSettings'))
      return false
    } finally {
      settingsSaving.value = false
    }
  }

  async function linkTransaction(transactionId: string, invoiceId: string): Promise<boolean> {
    linkError.value = ''
    linkingId.value = transactionId
    try {
      const { data } = await api.post<GoakalTransaction>(
        `/goakal/transactions/${transactionId}/link`,
        { invoiceId },
      )
      const index = items.value.findIndex((tx) => tx.id === data.id)
      if (index !== -1) items.value[index] = data
      return true
    } catch (e: any) {
      linkError.value = getErrorMessage(e, i18n.global.t('goakal.errors.link'))
      return false
    } finally {
      linkingId.value = null
    }
  }

  function reset(): void {
    listSeq++
    items.value = []
    total.value = 0
    page.value = 1
    listLoading.value = false
    listError.value = ''
    settings.value = null
    settingsLoading.value = false
    settingsError.value = ''
    settingsSaving.value = false
    settingsSaveError.value = ''
    linkError.value = ''
    linkingId.value = null
  }

  return {
    items,
    total,
    page,
    listLoading,
    listError,
    settings,
    settingsLoading,
    settingsError,
    settingsSaving,
    settingsSaveError,
    linkError,
    linkingId,
    fetchList,
    setPage,
    fetchSettings,
    saveSettings,
    linkTransaction,
    reset,
  }
})
