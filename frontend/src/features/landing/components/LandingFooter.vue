<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { brand } from '@/shared/brand'

const { t } = useI18n()
</script>

<template>
  <footer class="border-t border-outline-gray-1">
    <div
      class="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-5 py-8 sm:flex-row"
    >
      <div class="flex items-center gap-2">
        <span class="rounded-4 bg-surface-gray-2 p-1.5 text-ink-gray-6">
          <span class="lucide-package size-3.5" aria-hidden="true" />
        </span>
        <span class="text-p-sm-medium text-ink-gray-7">{{ brand.name }}</span>
        <span class="text-p-sm text-ink-gray-4">· {{ t('landing.footer.alpha') }}</span>
      </div>

      <nav class="flex flex-wrap items-center justify-center gap-4">
        <a
          href="/#features"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
        >
          {{ t('landing.nav.features') }}
        </a>
        <a
          href="/#about"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
        >
          {{ t('landing.nav.about') }}
        </a>
        <router-link
          :to="{ name: 'BlogList' }"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
        >
          {{ t('nav.blog') }}
        </router-link>
        <router-link
          :to="{ name: 'Login' }"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
        >
          {{ t('auth.signIn') }}
        </router-link>
        <router-link
          :to="{ name: 'Register' }"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
        >
          {{ t('landing.getStarted') }}
        </router-link>
      </nav>

      <p class="text-p-sm text-ink-gray-4">
        {{ t('landing.footer.copyright', { name: brand.name }) }}
      </p>
    </div>
  </footer>
</template>
