import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export const PLAN_TIERS = ['community', 'professional'] as const
export const DURATION_UNITS = ['days', 'months'] as const

export interface Plan {
  id: string
  name: string
  tier: string
  /** Absent when the plan is billed manually. */
  price?: number | null
  durationValue: number
  durationUnit: string
  features: Record<string, boolean>
  isDefault: boolean
  isActive: boolean
  createdOn: string | null
}

export interface PlanInput {
  name: string
  tier: string
  price: number | null
  durationValue: number
  durationUnit: string
  features?: Record<string, boolean>
  isDefault: boolean
  isActive: boolean
}

export interface FeatureCategory {
  key: string
  features: string[]
}

interface Paged<T> {
  items: T[]
  total: number
  page: number
  perPage: number
}

interface PlanQuery {
  search: string
  perPage: number
}

export function durationLabel(value: number, unit: string): string {
  const key = `plans.duration.${unit}`
  return i18n.global.te(key)
    ? i18n.global.t(key, { n: value })
    : `${value} ${unit}`
}

export const usePlansStore = defineStore('plans', () => {
  const items = ref<Plan[]>([])
  const options = ref<Plan[]>([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)
  const loadError = ref('')
  const featureKeys = ref<string[]>([])
  const featureCategories = ref<FeatureCategory[]>([])
  const featureKeysError = ref('')
  const actionError = ref('')
  const saving = ref(false)
  const deletingId = ref<string | null>(null)
  let listSeq = 0
  let lastQuery: PlanQuery = { search: '', perPage: 20 }
  let featureKeysInFlight: Promise<void> | null = null
  let optionsInFlight: Promise<void> | null = null

  async function fetchPlans(query?: PlanQuery): Promise<void> {
    if (query) lastQuery = query
    const seq = ++listSeq
    loading.value = true
    loadError.value = ''
    try {
      const { data } = await api.get<Paged<Plan>>('/plans', {
        params: {
          search: lastQuery.search.trim() || undefined,
          page: page.value,
          per_page: lastQuery.perPage,
        },
      })
      if (seq !== listSeq) return
      items.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? page.value
    } catch (e: any) {
      if (seq !== listSeq) return
      loadError.value = getErrorMessage(e, i18n.global.t('plans.errors.list'))
    } finally {
      if (seq === listSeq) loading.value = false
    }
  }

  function setPage(next: number): void {
    page.value = next
  }

  /** Full catalog for the subscription select, independent of list paging. */
  function fetchPlanOptions(): Promise<void> {
    if (options.value.length) return Promise.resolve()
    if (optionsInFlight) return optionsInFlight
    const request = api
      .get<Paged<Plan>>('/plans', { params: { page: 1, per_page: 200 } })
      .then(({ data }) => {
        options.value = data.items ?? []
      })
      .catch(() => {
        options.value = []
      })
      .finally(() => {
        optionsInFlight = null
      })
    optionsInFlight = request
    return request
  }

  function fetchFeatureKeys(): Promise<void> {
    if (featureKeys.value.length) return Promise.resolve()
    if (featureKeysInFlight) return featureKeysInFlight
    featureKeysError.value = ''
    const request = api
      .get<{ features: string[]; categories?: FeatureCategory[] }>('/plans/features')
      .then(({ data }) => {
        const keys = data.features ?? []
        featureKeys.value = keys
        featureCategories.value = data.categories?.length
          ? data.categories
          : [{ key: 'other', features: keys }]
      })
      .catch((e: any) => {
        featureKeysError.value = getErrorMessage(
          e,
          i18n.global.t('plans.errors.features'),
        )
      })
      .finally(() => {
        featureKeysInFlight = null
      })
    featureKeysInFlight = request
    return request
  }

  async function createPlan(payload: PlanInput): Promise<Plan | null> {
    actionError.value = ''
    saving.value = true
    try {
      const { data } = await api.post<Plan>('/plans', payload)
      options.value = []
      await fetchPlans()
      return data
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('plans.errors.create'))
      return null
    } finally {
      saving.value = false
    }
  }

  async function updatePlan(
    id: string,
    payload: Partial<PlanInput>,
  ): Promise<Plan | null> {
    actionError.value = ''
    saving.value = true
    try {
      const { data } = await api.put<Plan>(`/plans/${id}`, payload)
      options.value = []
      await fetchPlans()
      return data
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('plans.errors.update'))
      return null
    } finally {
      saving.value = false
    }
  }

  async function deletePlan(id: string): Promise<boolean> {
    actionError.value = ''
    deletingId.value = id
    try {
      await api.delete(`/plans/${id}`)
      options.value = []
      await fetchPlans()
      if (!items.value.length && page.value > 1) {
        page.value -= 1
        await fetchPlans()
      }
      return true
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('plans.errors.delete'))
      return false
    } finally {
      deletingId.value = null
    }
  }

  /** Drop catalog state so another account never sees the previous session's list. */
  function reset(): void {
    listSeq++
    items.value = []
    options.value = []
    total.value = 0
    page.value = 1
    loading.value = false
    loadError.value = ''
    featureKeys.value = []
    featureCategories.value = []
    featureKeysError.value = ''
    featureKeysInFlight = null
    optionsInFlight = null
    lastQuery = { search: '', perPage: 20 }
    actionError.value = ''
    saving.value = false
    deletingId.value = null
  }

  return {
    items,
    options,
    total,
    page,
    loading,
    loadError,
    featureKeys,
    featureCategories,
    featureKeysError,
    actionError,
    saving,
    deletingId,
    fetchPlans,
    setPage,
    fetchPlanOptions,
    fetchFeatureKeys,
    createPlan,
    updatePlan,
    deletePlan,
    reset,
  }
})
