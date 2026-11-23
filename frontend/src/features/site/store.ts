import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export interface ContactInput {
  name: string
  phone: string
  email?: string
  message: string
}

export const useContactStore = defineStore('contact', () => {
  const sending = ref(false)
  const sent = ref(false)
  const error = ref('')

  async function sendMessage(input: ContactInput): Promise<boolean> {
    sending.value = true
    sent.value = false
    error.value = ''
    try {
      await api.post('/contact/messages', input)
      sent.value = true
      return true
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('contactPage.errors.sendFailed'))
      return false
    } finally {
      sending.value = false
    }
  }

  function reset(): void {
    sent.value = false
    error.value = ''
  }

  return { sending, sent, error, sendMessage, reset }
})
