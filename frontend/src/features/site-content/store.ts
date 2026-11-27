import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'
import { setSiteContent, type SiteContent } from '@/shared/siteContent'

export const useSiteContentStore = defineStore('siteContent', () => {
  const content = ref<SiteContent | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')

  async function fetchContent(): Promise<SiteContent | null> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<SiteContent>('/site/content')
      content.value = data
      return data
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('siteContent.admin.loadFailed'),
      )
      return null
    } finally {
      loading.value = false
    }
  }

  async function saveContent(payload: Partial<SiteContent>): Promise<SiteContent | null> {
    saving.value = true
    error.value = ''
    try {
      const { data } = await api.patch<SiteContent>('/site/content', payload)
      content.value = data
      setSiteContent(data)
      return data
    } catch (e: any) {
      error.value = getErrorMessage(
        e,
        i18n.global.t('siteContent.admin.saveFailed'),
      )
      return null
    } finally {
      saving.value = false
    }
  }

  return { content, loading, saving, error, fetchContent, saveContent }
})
