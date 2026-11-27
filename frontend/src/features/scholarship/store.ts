import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface ScholarshipSummary {
  id: string
  title: string
  slug: string
  level: string
  excerpt: string
  coverImage?: string
  status: string
  order: number
  publishedOn?: string
  createdOn?: string
}

export interface ScholarshipDetail extends ScholarshipSummary {
  body: string
}

interface ScholarshipListResponse {
  items: ScholarshipSummary[]
  total: number
  page: number
  perPage: number
}

interface ScholarshipQuery {
  search?: string
  page?: number
  perPage?: number
}

export interface ScholarshipInput {
  title: string
  slug?: string
  level?: string
  body: string
  status: string
  coverImage?: string
  order?: number
}

export const useScholarshipStore = defineStore('scholarship', () => {
  const scholarships = ref<ScholarshipSummary[]>([])
  const scholarship = ref<ScholarshipDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const loadingScholarship = ref(false)
  const error = ref('')
  const checked = ref(false)

  function openGate(): void {
    checked.value = true
  }

  async function fetchList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ScholarshipListResponse>('/scholarship/scholarships', {
        params: { page: nextPage, per_page: perPage.value },
      })
      scholarships.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function fetchScholarship(slug: string): Promise<boolean> {
    loadingScholarship.value = true
    error.value = ''
    scholarship.value = null
    try {
      const { data } = await api.get<ScholarshipDetail>(`/scholarship/scholarships/${slug}`)
      scholarship.value = data
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.notFound'))
      return false
    } finally {
      loadingScholarship.value = false
      openGate()
    }
  }

  async function fetchAdminList(query: ScholarshipQuery = {}): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.search) params.search = query.search
      const { data } = await api.get<ScholarshipListResponse>('/scholarship/admin/scholarships', {
        params,
      })
      scholarships.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? 1
      perPage.value = data.perPage ?? perPage.value
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function createScholarship(input: ScholarshipInput): Promise<ScholarshipDetail | null> {
    error.value = ''
    try {
      const { data } = await api.post<ScholarshipDetail>('/scholarship/scholarships', input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.createFailed'))
      return null
    }
  }

  async function updateScholarship(
    slug: string,
    input: Partial<ScholarshipInput>,
  ): Promise<ScholarshipDetail | null> {
    error.value = ''
    try {
      const { data } = await api.patch<ScholarshipDetail>(`/scholarship/scholarships/${slug}`, input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.updateFailed'))
      return null
    }
  }

  async function removeScholarship(slug: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/scholarship/scholarships/${slug}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('scholarship.errors.deleteFailed'))
      return false
    }
  }

  function clearError(): void {
    error.value = ''
  }

  return {
    scholarships,
    scholarship,
    total,
    page,
    perPage,
    loading,
    loadingScholarship,
    error,
    checked,
    clearError,
    openGate,
    fetchList,
    fetchScholarship,
    fetchAdminList,
    createScholarship,
    updateScholarship,
    removeScholarship,
  }
})
