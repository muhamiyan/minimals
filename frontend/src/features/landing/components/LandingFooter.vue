<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/features/auth/store'
import BrandLogo from '@/shared/components/BrandLogo.vue'
import { brand } from '@/shared/brand'
import { GITHUB_URL, navLinks } from '../content'
import { useLandingContent } from '../useLandingContent'

const { t } = useI18n()
const auth = useAuthStore()
const { footer } = useLandingContent()
</script>

<template>
  <footer class="border-t border-outline-gray-1">
    <div
      class="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-5 py-8 sm:flex-row"
    >
      <div class="flex items-center gap-2.5">
        <div class="size-8 shrink-0 overflow-hidden rounded-4">
          <BrandLogo size="fill" :alt="brand.name">
            <span
              class="flex h-full w-full items-center justify-center bg-surface-blue-6 text-white"
            >
              <span class="lucide-package size-4" aria-hidden="true" />
            </span>
          </BrandLogo>
        </div>
        <div class="min-w-0">
          <router-link
            :to="{ name: 'Landing' }"
            class="block truncate text-p-sm-medium text-ink-gray-7 transition-colors hover:text-ink-gray-9 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
          >
            {{ brand.name }}
          </router-link>
          <a
            :href="GITHUB_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="mt-0.5 inline-flex items-center gap-1.5 text-p-sm text-ink-gray-5 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
          >
            <span class="truncate">{{ footer.githubTagline }}</span>
            <span class="lucide-github size-3.5 shrink-0" aria-hidden="true" />
          </a>
        </div>
      </div>

      <nav class="flex flex-wrap items-center justify-center gap-4">
        <a
          v-for="link in navLinks"
          :key="link.id"
          :href="`/#${link.id}`"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          {{ t(link.key) }}
        </a>
        <router-link
          :to="{ name: 'BlogList' }"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          {{ t('nav.blog') }}
        </router-link>
        <router-link
          v-if="!auth.user"
          :to="{ name: 'Login' }"
          class="text-p-sm text-ink-gray-5 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          {{ t('auth.signIn') }}
        </router-link>
      </nav>

      <div class="text-center sm:text-right">
        <p class="text-p-sm text-ink-gray-4">
          {{ t('landing.footer.copyright', { name: brand.name }) }}
        </p>
        <p class="mt-1 text-p-sm text-ink-gray-4">{{ footer.license }}</p>
      </div>
    </div>
  </footer>
</template>
