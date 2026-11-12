import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface StatsMonthRow {
  month: string
  count: number
}

export interface StatsAmountRow {
  month: string
  amount: number
}

export type SubscriptionStatus = 'trial' | 'active' | 'expired' | 'cancelled'
export type InvoiceStatus = 'issued' | 'paid' | 'void'

export interface DashboardStats {
  organizations: { total: number; active: number }
  users: { total: number }
  subscriptions: Record<SubscriptionStatus, number>
  invoices: Record<InvoiceStatus, number>
  revenuePaid: number
  organizationsPerMonth: StatsMonthRow[]
  revenuePerMonth: StatsAmountRow[]
}

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchStats(): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<DashboardStats>('/dashboard/stats')
      stats.value = data
      return true
    } catch (e: unknown) {
      stats.value = null
      error.value = getErrorMessage(e, i18n.global.t('dash.super.loadFailed'))
      return false
    } finally {
      loading.value = false
    }
  }

  function reset(): void {
    stats.value = null
    loading.value = false
    error.value = ''
  }

  return { stats, loading, error, fetchStats, reset }
})
