<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'

import { useAuthStore } from '../store'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const identifier = ref('')
const password = ref('')
const submitting = ref(false)

const errorMessage = computed(() => auth.error)
const disabled = computed(() => submitting.value || !identifier.value.trim() || !password.value)

async function onSubmit() {
  if (disabled.value) return
  submitting.value = true
  const ok = await auth.login(identifier.value.trim(), password.value)
  submitting.value = false
  if (ok) {
    toast.success(`Welcome back, ${auth.user?.fullName ?? auth.user?.email}`)
    const next = (route.query.redirect as string) || '/'
    if (!next.startsWith('/') || next.startsWith('//')) return router.replace('/')
    router.replace(next)
  }
}
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8"
  >
    <div class="w-full max-w-sm rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6">
      <form class="space-y-4" @submit.prevent="onSubmit">
        <div class="flex flex-col items-center gap-1.5 text-center">
          <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
            <span class="lucide-package size-6" aria-hidden="true" />
          </div>
          <h1 class="text-2xl-semibold text-ink-gray-8">Sign in</h1>
          <p class="text-p-sm text-ink-gray-5">Minimals</p>
        </div>

        <ErrorMessage v-if="errorMessage" :message="errorMessage" />

        <FormControl
          v-model="identifier"
          label="Email or username"
          placeholder="abdulah@example.com"
          autocomplete="username"
          required
        />
        <FormControl
          v-model="password"
          type="password"
          label="Password"
          placeholder="••••••••"
          autocomplete="current-password"
          required
        />

        <Button
          type="submit"
          variant="solid"
          theme="gray"
          icon-left="lucide-log-in"
          label="Sign in"
          :loading="submitting"
          :disabled="disabled"
        />

        <p class="text-center text-p-sm text-ink-gray-5">
          No account?
          <router-link :to="{ name: 'Register' }" class="text-ink-blue-link">
            Create one
          </router-link>
        </p>
      </form>
    </div>
  </div>
</template>
