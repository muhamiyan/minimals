<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, useColorScheme } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import BrandLogo from '@/shared/components/BrandLogo.vue'
import { brand } from '@/shared/brand'
import { navLinks } from '../content'
import { useStartAction } from '../useStartAction'

const { t } = useI18n()
const auth = useAuthStore()
const { loading, start } = useStartAction()

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const themeIcon = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
)

</script>

<template>
  <header
    class="sticky top-0 z-40 border-b border-outline-gray-1 bg-surface-base/80 backdrop-blur-md"
  >
    <div class="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-3 px-5">
      <router-link
        :to="{ name: 'Landing' }"
        class="flex items-center gap-2 rounded-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
      >
        <div class="size-8 shrink-0 overflow-hidden rounded-4">
          <BrandLogo size="fill" :alt="brand.name">
            <span
              class="flex h-full w-full items-center justify-center bg-surface-blue-6 text-white"
            >
              <span class="lucide-package size-4" aria-hidden="true" />
            </span>
          </BrandLogo>
        </div>
        <span class="text-base-semibold text-ink-gray-9">{{ brand.name }}</span>
      </router-link>

      <nav class="hidden items-center gap-1 sm:flex">
        <a
          v-for="link in navLinks"
          :key="link.key"
          :href="`/#${link.id}`"
          class="rounded-4 px-3 py-1.5 text-base-medium text-ink-gray-6 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          {{ t(link.key) }}
        </a>
        <router-link
          :to="{ name: 'BlogList' }"
          class="rounded-4 px-3 py-1.5 text-base-medium text-ink-gray-6 transition-colors hover:text-surface-blue-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          {{ t('nav.blog') }}
        </router-link>
      </nav>

      <div class="flex items-center gap-2">
        <Button
          :icon="themeIcon"
          :label="t('landing.nav.theme')"
          size="sm"
          variant="ghost"
          @click="toggleColorScheme"
        />
        <template v-if="!auth.user">
          <Button
            :label="t('auth.signIn')"
            size="sm"
            variant="ghost"
            class="hidden sm:inline-flex"
            :route="{ name: 'Login' }"
          />
          <Button
            :label="t('landing.getStarted')"
            size="sm"
            variant="solid"
            theme="blue"
            :loading="loading"
            @click="start"
          />
        </template>
        <Button
          v-else
          :label="t('nav.dashboard')"
          size="sm"
          variant="solid"
          theme="blue"
          icon-left="lucide-layout-dashboard"
          :loading="loading"
          @click="start"
        />
      </div>
    </div>

    <nav
      class="no-scrollbar flex items-center gap-1 overflow-x-auto border-t border-outline-gray-1 px-3 py-2 sm:hidden"
    >
      <a
        v-for="link in navLinks"
        :key="link.id"
        :href="`/#${link.id}`"
        class="shrink-0 rounded-4 px-2.5 py-1 text-p-sm-medium text-ink-gray-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
      >
        {{ t(link.key) }}
      </a>
    </nav>
  </header>
</template>
