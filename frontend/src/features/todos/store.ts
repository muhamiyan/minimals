import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export type TodoStatusFilter = 'all' | 'open' | 'done'

export interface Todo {
  id: string
  title: string
  /** Presenter omits null fields. */
  description?: string | null
  completed: boolean
  dueDate?: string | null
  createdBy: string
  createdOn: string | null
  changedOn: string | null
}

export interface TodoInput {
  title: string
  description?: string | null
  completed?: boolean
  dueDate?: string | null
}

export interface TodoQuery {
  search: string
  perPage: number
  completed: TodoStatusFilter
}

interface Paged<T> {
  items: T[]
  total: number
  page: number
  perPage: number
}

export const useTodosStore = defineStore('todos', () => {
  const items = ref<Todo[]>([])
  const total = ref(0)
  const page = ref(1)
  const loading = ref(false)
  const error = ref('')
  const saving = ref(false)
  const deletingId = ref<string | null>(null)
  let listSeq = 0
  let lastQuery: TodoQuery = { search: '', perPage: 20, completed: 'all' }

  function baseUrl(orgId: string): string {
    return `/todos/organizations/${orgId}`
  }

  async function list(orgId: string, query?: TodoQuery): Promise<void> {
    if (query) lastQuery = query
    const seq = ++listSeq
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<Paged<Todo>>(baseUrl(orgId), {
        params: {
          search: lastQuery.search.trim() || undefined,
          completed:
            lastQuery.completed === 'all' ? undefined : lastQuery.completed === 'done',
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
      error.value = getErrorMessage(e, i18n.global.t('todos.errors.list'))
    } finally {
      if (seq === listSeq) loading.value = false
    }
  }

  function setPage(next: number): void {
    page.value = next
  }

  async function create(orgId: string, payload: TodoInput): Promise<Todo | null> {
    error.value = ''
    saving.value = true
    try {
      const { data } = await api.post<Todo>(baseUrl(orgId), payload)
      // Newest first: jump to the first page so the created row is visible.
      page.value = 1
      await list(orgId)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.errors.save'))
      return null
    } finally {
      saving.value = false
    }
  }

  async function update(
    orgId: string,
    id: string,
    payload: Partial<TodoInput>,
  ): Promise<Todo | null> {
    error.value = ''
    saving.value = true
    try {
      const { data } = await api.put<Todo>(`${baseUrl(orgId)}/${id}`, payload)
      await list(orgId)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.errors.save'))
      return null
    } finally {
      saving.value = false
    }
  }

  async function remove(orgId: string, id: string): Promise<boolean> {
    error.value = ''
    deletingId.value = id
    try {
      await api.delete(`${baseUrl(orgId)}/${id}`)
      await list(orgId)
      if (!items.value.length && page.value > 1) {
        page.value -= 1
        await list(orgId)
      }
      return true
    } catch (e: any) {
      error.value = getErrorMessage(e, i18n.global.t('todos.errors.delete'))
      return false
    } finally {
      deletingId.value = null
    }
  }

  /** Drop list state so another account or organization never sees stale rows. */
  function reset(): void {
    listSeq++
    items.value = []
    total.value = 0
    page.value = 1
    loading.value = false
    error.value = ''
    saving.value = false
    deletingId.value = null
    lastQuery = { search: '', perPage: 20, completed: 'all' }
  }

  return {
    items,
    total,
    page,
    loading,
    error,
    saving,
    deletingId,
    list,
    setPage,
    create,
    update,
    remove,
    reset,
  }
})
