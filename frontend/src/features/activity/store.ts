import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface ActivitySummary {
  id: string
  title: string
  slug: string
  excerpt: string
  coverImage?: string
  status: string
  publishedOn?: string
  createdOn?: string
  authorName?: string
}

export interface ActivityDetail extends ActivitySummary {
  body: string
}

interface ActivityListResponse {
  items: ActivitySummary[]
  total: number
  page: number
  perPage: number
}

export interface ActivityInput {
  title: string
  slug?: string
  body: string
  status: string
  coverImage?: string
}

export const useActivityStore = defineStore('activity', () => {
  const activities = ref<ActivitySummary[]>([])
  const activity = ref<ActivityDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(10)
  const loading = ref(false)
  const loadingActivity = ref(false)
  const error = ref('')
  const checked = ref(false)

  function openGate(): void {
    checked.value = true
  }

  async function fetchList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ActivityListResponse>('/activity/activities', {
        params: { page: nextPage, per_page: perPage.value },
      })
      activities.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function fetchActivity(slug: string): Promise<boolean> {
    loadingActivity.value = true
    error.value = ''
    activity.value = null
    try {
      const { data } = await api.get<ActivityDetail>(`/activity/activities/${slug}`)
      activity.value = data
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.notFound'))
      return false
    } finally {
      loadingActivity.value = false
      openGate()
    }
  }

  async function fetchAdminList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ActivityListResponse>('/activity/admin/activities', {
        params: { page: nextPage, per_page: perPage.value },
      })
      activities.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function createActivity(input: ActivityInput): Promise<ActivityDetail | null> {
    error.value = ''
    try {
      const { data } = await api.post<ActivityDetail>('/activity/activities', input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.createFailed'))
      return null
    }
  }

  async function updateActivity(
    slug: string,
    input: Partial<ActivityInput>,
  ): Promise<ActivityDetail | null> {
    error.value = ''
    try {
      const { data } = await api.patch<ActivityDetail>(
        `/activity/activities/${slug}`,
        input,
      )
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.updateFailed'))
      return null
    }
  }

  async function removeActivity(slug: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/activity/activities/${slug}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('activity.errors.deleteFailed'))
      return false
    }
  }

  function clearError(): void {
    error.value = ''
  }

  return {
    activities,
    activity,
    total,
    page,
    perPage,
    loading,
    loadingActivity,
    error,
    checked,
    clearError,
    openGate,
    fetchList,
    fetchActivity,
    fetchAdminList,
    createActivity,
    updateActivity,
    removeActivity,
  }
})
