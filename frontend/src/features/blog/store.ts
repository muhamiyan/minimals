import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, getErrorMessage } from '@/shared/api'

export interface BlogSummary {
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

export interface BlogPostDetail extends BlogSummary {
  body: string
}

interface BlogListResponse {
  items: BlogSummary[]
  total: number
  page: number
  perPage: number
}

export interface BlogPostInput {
  title: string
  slug?: string
  body: string
  status: string
  coverImage?: string
}

export const useBlogStore = defineStore('blog', () => {
  const posts = ref<BlogSummary[]>([])
  const post = ref<BlogPostDetail | null>(null)
  const total = ref(0)
  const page = ref(1)
  const perPage = ref(10)
  const loading = ref(false)
  const loadingPost = ref(false)
  const error = ref('')

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
      error.value = getErrorMessage(e, 'Could not load posts')
      return false
    } finally {
      loading.value = false
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
      error.value = getErrorMessage(e, 'Post not found')
      return false
    } finally {
      loadingPost.value = false
    }
  }

  async function fetchAdminList(nextPage = 1): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<BlogListResponse>('/blog/admin/posts', {
        params: { page: nextPage, per_page: perPage.value },
      })
      posts.value = data.items
      total.value = data.total
      page.value = data.page
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, 'Could not load posts')
      return false
    } finally {
      loading.value = false
    }
  }

  async function createPost(input: BlogPostInput): Promise<BlogPostDetail | null> {
    error.value = ''
    try {
      const { data } = await api.post<BlogPostDetail>('/blog/posts', input)
      return data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, 'Could not create post')
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
      error.value = getErrorMessage(e, 'Could not update post')
      return null
    }
  }

  async function removePost(slug: string): Promise<boolean> {
    error.value = ''
    try {
      await api.delete(`/blog/posts/${slug}`)
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, 'Could not delete post')
      return false
    }
  }

  function clearError(): void {
    error.value = ''
  }

  return {
    posts,
    post,
    total,
    page,
    perPage,
    loading,
    loadingPost,
    error,
    clearError,
    fetchList,
    fetchPost,
    fetchAdminList,
    createPost,
    updatePost,
    removePost,
  }
})
