<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, useColorScheme } from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { brand, logoBackdropClass, useBrandLogo } from '@/shared/brand'

const { t } = useI18n()
const auth = useAuthStore()
const { logoSrc, logoTone, onLogoError } = useBrandLogo()

const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const mobileMenu = ref<HTMLDetailsElement | null>(null)

function closeMobileMenu() {
  if (mobileMenu.value) mobileMenu.value.open = false
}

const themeIcon = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
)

const homeLinks = [{ key: 'landing.nav.home', name: 'Landing' }]

const infoLinks = [
  { key: 'landing.nav.profile', name: 'Profile' },
  { key: 'landing.nav.ppdb', name: 'Ppdb' },
  { key: 'landing.nav.structure', name: 'Structure' },
  { key: 'landing.nav.facilities', name: 'Facilities' },
  { key: 'landing.nav.programs', name: 'ProgramList' },
]

const routeLinks = [
  { key: 'landing.nav.scholarships', name: 'ScholarshipList' },
  { key: 'landing.nav.activities', name: 'ActivityList' },
  { key: 'landing.nav.gallery', name: 'Gallery' },
  { key: 'nav.blog', name: 'BlogList' },
  { key: 'landing.nav.contact', name: 'Contact' },
]

function goTop() {
  if (window.location.hash) {
    history.replaceState(window.history.state, '', window.location.pathname)
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <header
    class="sticky top-0 z-40 border-b border-outline-green-2 bg-surface-green-1/80 backdrop-blur-md dark:bg-surface-green-2/70"
  >
    <div class="mx-auto flex h-14 w-full max-w-6xl items-center justify-between gap-3 px-5">
      <router-link
        :to="{ name: 'Landing' }"
        class="flex min-w-0 items-center gap-2 rounded-4"
        @click="goTop"
      >
        <span
          class="flex size-7 items-center justify-center rounded-4"
          :class="logoBackdropClass(logoTone)"
        >
          <img
            v-if="logoSrc"
            :src="logoSrc"
            alt=""
            class="size-full rounded-4 object-contain"
            @error="onLogoError"
          />
          <span v-else class="text-ink-green-7">
            <span class="lucide-school size-4" aria-hidden="true" />
          </span>
        </span>
        <span class="truncate text-base-semibold text-ink-gray-9">{{ brand.name }}</span>
      </router-link>

      <nav class="hidden items-center gap-0.5 lg:flex">
        <router-link
          v-for="link in homeLinks"
          :key="link.key"
          :to="{ name: link.name }"
          class="rounded-4 px-2 py-1.5 text-sm-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
        >
          {{ t(link.key) }}
        </router-link>

        <div class="group relative">
          <Button
            :label="t('landing.nav.information')"
            size="sm"
            variant="ghost"
            icon-right="lucide-chevron-down"
          />
          <div
            class="invisible absolute left-0 top-full z-10 w-48 rounded-6 border border-outline-green-2 bg-surface-elevation-2 p-1 opacity-0 shadow-lg transition-opacity group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100"
          >
            <router-link
              v-for="link in infoLinks"
              :key="link.key"
              :to="{ name: link.name }"
              class="block rounded-4 px-3 py-2 text-p-sm text-ink-gray-7 transition-colors hover:bg-surface-green-1 hover:text-ink-gray-9"
            >
              {{ t(link.key) }}
            </router-link>
          </div>
        </div>

        <router-link
          v-for="link in routeLinks"
          :key="link.key"
          :to="{ name: link.name }"
          class="rounded-4 px-2 py-1.5 text-sm-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
        >
          {{ t(link.key) }}
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
        </template>
        <Button
          v-else
          :label="t('nav.dashboard')"
          size="sm"
          variant="solid"
          theme="green"
          icon-left="lucide-layout-dashboard"
          :route="{ name: 'Dashboard' }"
        />
        <details ref="mobileMenu" class="relative lg:hidden">
          <summary
            class="flex size-8 cursor-pointer list-none items-center justify-center rounded-4 border border-outline-green-2 bg-surface-elevation-2 text-ink-gray-7 [&::-webkit-details-marker]:hidden"
            :aria-label="t('landing.nav.menu')"
          >
            <span class="lucide-menu size-4" aria-hidden="true" />
          </summary>
          <div
            class="absolute right-0 top-10 z-20 w-56 rounded-6 border border-outline-green-2 bg-surface-elevation-2 p-1 shadow-lg"
          >
            <router-link
              v-for="link in homeLinks"
              :key="link.key"
              :to="{ name: link.name }"
              class="block rounded-4 px-3 py-2 text-p-sm text-ink-gray-7"
              @click="closeMobileMenu"
            >
              {{ t(link.key) }}
            </router-link>
            <router-link
              v-for="link in infoLinks"
              :key="link.key"
              :to="{ name: link.name }"
              class="block rounded-4 px-3 py-2 text-p-sm text-ink-gray-7"
              @click="closeMobileMenu"
            >
              {{ t(link.key) }}
            </router-link>
            <router-link
              v-for="link in routeLinks"
              :key="link.key"
              :to="{ name: link.name }"
              class="block rounded-4 px-3 py-2 text-p-sm text-ink-gray-7"
              @click="closeMobileMenu"
            >
              {{ t(link.key) }}
            </router-link>
          </div>
        </details>
      </div>
    </div>
  </header>
</template>
