import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/features/auth/store'

export function useStartAction() {
  const router = useRouter()
  const auth = useAuthStore()
  const loading = ref(false)

  async function start(): Promise<void> {
    if (loading.value) return
    loading.value = true
    try {
      await router.push({ name: auth.user ? 'Dashboard' : 'Register' })
    } finally {
      loading.value = false
    }
  }

  return { loading, start }
}
