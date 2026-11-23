import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface ProgramSummary {
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

export interface ProgramDetail extends ProgramSummary {
  body: string
}

interface ProgramListResponse {
  items: ProgramSummary[]
  total: number
  page: number
  perPage: number
}

export interface ProgramInput {
  title: string
  slug?: string
  level?: string
  body: string
  status: string
  coverImage?: string
  order?: number
}

export const useProgramStore = defineStore('program', () => {
  const programs = ref<ProgramSummary[]>([])
  const program = ref<ProgramDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(20)
  const loading = ref(false)
  const loadingProgram = ref(false)
  const error = ref('')
  const checked = ref(false)

  function openGate(): void {
    checked.value = true
  }

  async function fetchList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ProgramListResponse>('/program/programs', {
        params: { page: nextPage, per_page: perPage.value },
      })
      programs.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function fetchProgram(slug: string): Promise<boolean> {
    loadingProgram.value = true
    error.value = ''
    program.value = null
    try {
      const { data } = await api.get<ProgramDetail>(`/program/programs/${slug}`)
      program.value = data
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.notFound'))
      return false
    } finally {
      loadingProgram.value = false
      openGate()
    }
  }

  async function fetchAdminList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<ProgramListResponse>('/program/admin/programs', {
        params: { page: nextPage, per_page: perPage.value },
      })
      programs.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function createProgram(input: ProgramInput): Promise<ProgramDetail | null> {
    error.value = ''
    try {
      const { data } = await api.post<ProgramDetail>('/program/programs', input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.createFailed'))
      return null
    }
  }

  async function updateProgram(
    slug: string,
    input: Partial<ProgramInput>,
  ): Promise<ProgramDetail | null> {
    error.value = ''
    try {
      const { data } = await api.patch<ProgramDetail>(`/program/programs/${slug}`, input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.updateFailed'))
      return null
    }
  }

  async function removeProgram(slug: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/program/programs/${slug}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('program.errors.deleteFailed'))
      return false
    }
  }

  function clearError(): void {
    error.value = ''
  }

  return {
    programs,
    program,
    total,
    page,
    perPage,
    loading,
    loadingProgram,
    error,
    checked,
    clearError,
    openGate,
    fetchList,
    fetchProgram,
    fetchAdminList,
    createProgram,
    updateProgram,
    removeProgram,
  }
})
