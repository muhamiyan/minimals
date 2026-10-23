<script setup lang="ts">
import { computed } from 'vue'
import { Button, useColorScheme } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { brand } from '@/shared/brand'
import { useStartAction } from '../useStartAction'

const auth = useAuthStore()
const { loading, start } = useStartAction()

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const themeIcon = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
)

function goTop() {
  if (window.location.hash) {
    history.replaceState(window.history.state, '', window.location.pathname)
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <header
    class="sticky top-0 z-40 border-b border-outline-gray-1 bg-surface-base/80 backdrop-blur-md"
  >
    <div class="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-3 px-5">
      <a
        href="#top"
        class="flex items-center gap-2 rounded-4"
        @click.prevent="goTop"
      >
        <span class="rounded-4 bg-surface-gray-2 p-1.5 text-ink-gray-7">
          <span class="lucide-package size-4" aria-hidden="true" />
        </span>
        <span class="text-base-semibold text-ink-gray-9">{{ brand.name }}</span>
      </a>

      <nav class="hidden items-center gap-1 sm:flex">
        <a
          href="/#features"
          class="rounded-4 px-3 py-1.5 text-base-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
        >
          Features
        </a>
        <a
          href="/#about"
          class="rounded-4 px-3 py-1.5 text-base-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
        >
          About
        </a>
        <router-link
          :to="{ name: 'BlogList' }"
          class="rounded-4 px-3 py-1.5 text-base-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
        >
          Blog
        </router-link>
      </nav>

      <div class="flex items-center gap-2">
        <Button
          :icon="themeIcon"
          label="Toggle theme"
          size="sm"
          variant="ghost"
          @click="toggleColorScheme"
        />
        <template v-if="!auth.user">
          <Button
            label="Sign in"
            size="sm"
            variant="ghost"
            class="hidden sm:inline-flex"
            :route="{ name: 'Login' }"
          />
          <Button
            label="Get started"
            size="sm"
            variant="solid"
            theme="blue"
            :loading="loading"
            @click="start"
          />
        </template>
        <Button
          v-else
          label="Dashboard"
          size="sm"
          variant="solid"
          theme="blue"
          icon-left="lucide-layout-dashboard"
          :loading="loading"
          @click="start"
        />
      </div>
    </div>
  </header>
</template>
