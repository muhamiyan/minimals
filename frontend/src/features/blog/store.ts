import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'
import { i18n } from '@/app/i18n'

export interface BlogSummary {
  id: string
  title: string
  slug: string
  excerpt: string
  author?: string
  category?: string
  readTime: number
  coverImage?: string
  status: string
  publishedOn?: string
  createdOn?: string
  authorName?: string
}

export interface BlogPostDetail extends BlogSummary {
  body: string
}

interface BlogListResponse {
  items: BlogSummary[]
  total: number
  page: number
  perPage: number
}

export interface BlogQuery {
  search?: string
  page?: number
  perPage?: number
}

export interface BlogCategory {
  id: string
  name: string
}

export interface BlogPostInput {
  title: string
  slug?: string
  body: string
  status: string
  coverImage?: string
  author?: string
  category?: string
}

export const useBlogStore = defineStore('blog', () => {
  const posts = ref<BlogSummary[]>([])
  const post = ref<BlogPostDetail | null>(null)
  const categories = ref<BlogCategory[]>([])
  const categoryError = ref('')
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(10)
  const loading = ref(false)
  const loadingPost = ref(false)
  const error = ref('')
  const checked = ref(false)

  function openGate(): void {
    checked.value = true
  }

  async function fetchList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<BlogListResponse>('/blog/posts', {
        params: { page: nextPage, per_page: perPage.value },
      })
      posts.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function fetchPost(slug: string): Promise<boolean> {
    loadingPost.value = true
    error.value = ''
    post.value = null
    try {
      const { data } = await api.get<BlogPostDetail>(`/blog/posts/${slug}`)
      post.value = data
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.notFound'))
      return false
    } finally {
      loadingPost.value = false
      openGate()
    }
  }

  async function fetchAdminList(query: BlogQuery = {}): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const params: Record<string, string | number> = {
        page: query.page ?? page.value,
        per_page: query.perPage ?? perPage.value,
      }
      if (query.search) params.search = query.search
      const { data } = await api.get<BlogListResponse>('/blog/admin/posts', { params })
      posts.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? 1
      perPage.value = data.perPage ?? perPage.value
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.loadFailed'))
      return false
    } finally {
      loading.value = false
      openGate()
    }
  }

  async function createPost(input: BlogPostInput): Promise<BlogPostDetail | null> {
    error.value = ''
    try {
      const { data } = await api.post<BlogPostDetail>('/blog/posts', input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.createFailed'))
      return null
    }
  }

  async function updatePost(
    slug: string,
    input: Partial<BlogPostInput>,
  ): Promise<BlogPostDetail | null> {
    error.value = ''
    try {
      const { data } = await api.patch<BlogPostDetail>(`/blog/posts/${slug}`, input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.updateFailed'))
      return null
    }
  }

  async function removePost(slug: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/blog/posts/${slug}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('blog.errors.deleteFailed'))
      return false
    }
  }

  async function fetchCategories(): Promise<boolean> {
    categoryError.value = ''
    try {
      const { data } = await api.get<{ items: BlogCategory[] }>('/blog/categories')
      categories.value = data.items ?? []
      return true
    } catch (e: unknown) {
      categoryError.value = getErrorMessage(e, i18n.global.t('blog.errors.loadFailed'))
      return false
    }
  }

  async function createCategory(name: string): Promise<BlogCategory | null> {
    categoryError.value = ''
    try {
      const { data } = await api.post<BlogCategory>('/blog/categories', { name })
      if (!categories.value.some((item) => item.id === data.id)) {
        categories.value.push(data)
      }
      categories.value.sort((a, b) => a.name.localeCompare(b.name))
      return data
    } catch (e: unknown) {
      categoryError.value = getErrorMessage(e, i18n.global.t('blog.errors.createFailed'))
      return null
    }
  }

  function clearError(): void {
    error.value = ''
  }

  return {
    posts,
    post,
    categories,
    categoryError,
    total,
    page,
    perPage,
    loading,
    loadingPost,
    error,
    checked,
    clearError,
    openGate,
    fetchList,
    fetchPost,
    fetchAdminList,
    fetchCategories,
    createCategory,
    createPost,
    updatePost,
    removePost,
  }
})
