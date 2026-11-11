import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'
import type { Plan } from '@/features/plans/store'
import type { Invoice } from '@/features/billing/store'

export const usePlanStore = defineStore('plan', () => {
  const items = ref<Plan[]>([])
  const loading = ref(false)
  const loadError = ref('')
  const actionError = ref('')
  const switchingId = ref<string | null>(null)
  /** An unpaid switch invoice blocks further switches until it is paid or voided. */
  const pendingInvoice = ref<Invoice | null>(null)

  async function fetchCatalog(): Promise<void> {
    loading.value = true
    loadError.value = ''
    try {
      const { data } = await api.get<{ items: Plan[] }>('/plans/catalog')
      items.value = data.items ?? []
    } catch (e: any) {
      loadError.value = getErrorMessage(e, i18n.global.t('plan.errors.load'))
    } finally {
      loading.value = false
    }
  }

  async function fetchPending(orgId: string): Promise<void> {
    try {
      const { data } = await api.get<{ items: Invoice[] }>(
        `/billing/organizations/${orgId}/invoices`,
        { params: { status: 'issued', per_page: 20 } },
      )
      pendingInvoice.value =
        (data.items ?? []).find((i) => i.planId && i.status === 'issued') ?? null
    } catch {
      // The banner is best-effort; the backend still rejects a second
      // switch with plan_switch_pending.
      pendingInvoice.value = null
    }
  }

  async function switchPlan(orgId: string, planId: string): Promise<Invoice | null> {
    actionError.value = ''
    switchingId.value = planId
    try {
      const { data } = await api.post<Invoice>(
        `/billing/organizations/${orgId}/plan-switch`,
        { planId },
      )
      pendingInvoice.value = data
      return data
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('plan.errors.switch'))
      return null
    } finally {
      switchingId.value = null
    }
  }

  function reset(): void {
    items.value = []
    loading.value = false
    loadError.value = ''
    actionError.value = ''
    switchingId.value = null
    pendingInvoice.value = null
  }

  return {
    items,
    loading,
    loadError,
    actionError,
    switchingId,
    pendingInvoice,
    fetchCatalog,
    fetchPending,
    switchPlan,
    reset,
  }
})
