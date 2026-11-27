<script setup lang="ts">
import { contentValue } from '@/shared/siteContent'
import { useI18n } from 'vue-i18n'

import { brand, logoBackdropClass, useBrandLogo } from '@/shared/brand'
import { contact } from '../content'

const { t } = useI18n()
const { logoSrc, logoTone, onLogoError } = useBrandLogo()

const links = [{ key: 'landing.nav.home', href: '/#top' }]

const routeLinks = [
  { key: 'landing.nav.ppdb', name: 'Ppdb' },
  { key: 'landing.nav.profile', name: 'Profile' },
  { key: 'landing.nav.structure', name: 'Structure' },
  { key: 'landing.nav.facilities', name: 'Facilities' },
  { key: 'landing.nav.programs', name: 'ProgramList' },
  { key: 'landing.nav.scholarships', name: 'ScholarshipList' },
  { key: 'landing.nav.activities', name: 'ActivityList' },
  { key: 'landing.nav.gallery', name: 'Gallery' },
  { key: 'landing.nav.contact', name: 'Contact' },
  { key: 'nav.blog', name: 'BlogList' },
]
</script>

<template>
  <footer class="border-t border-outline-green-2">
    <div class="mx-auto w-full max-w-6xl px-5 py-12">
      <div class="grid gap-10 md:grid-cols-3">
        <div>
          <router-link
            :to="{ name: 'Landing' }"
            class="flex items-center gap-2"
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
                <span class="lucide-school size-3.5" aria-hidden="true" />
              </span>
            </span>
            <span class="text-base-semibold text-ink-gray-8">{{ brand.name }}</span>
          </router-link>
          <p class="mt-3 max-w-xs text-p-sm text-ink-gray-5">
            {{ brand.tagline || t('landing.footer.tagline') }}
          </p>
          <p class="mt-3 text-p-sm text-ink-gray-5">
            {{ contentValue('contact.address', contact.address) }}
          </p>
        </div>

        <div>
          <h2 class="text-p-sm-medium text-ink-gray-8">{{ t('landing.footer.links') }}</h2>
          <nav class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
            <a
              v-for="link in links"
              :key="link.key"
              :href="link.href"
              class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
            >
              {{ t(link.key) }}
            </a>
            <router-link
              v-for="link in routeLinks"
              :key="link.key"
              :to="{ name: link.name }"
              class="text-p-sm text-ink-gray-5 transition-colors hover:text-ink-gray-8"
            >
              {{ t(link.key) }}
            </router-link>
          </nav>
        </div>

        <div>
          <h2 class="text-p-sm-medium text-ink-gray-8">{{ t('landing.contact.badge') }}</h2>
          <div class="mt-3 space-y-2 text-p-sm text-ink-gray-5">
            <a
              :href="`mailto:${contentValue('contact.email', contact.email)}`"
              class="block hover:text-ink-gray-8"
            >
              {{ contentValue('contact.email', contact.email) }}
            </a>
            <a
              :href="contentValue('contact.whatsappUrl', contact.whatsapp)"
              target="_blank"
              rel="noopener noreferrer"
              class="block hover:text-ink-gray-8"
            >
              WhatsApp · {{ contentValue('contact.whatsappDisplay', '0878 6470 6565') }}
            </a>
            <a
              :href="contentValue('contact.facebookUrl', contact.facebook)"
              target="_blank"
              rel="noopener noreferrer"
              class="block hover:text-ink-gray-8"
            >
              Facebook · {{ contentValue('contact.facebookDisplay', 'manw.selaparangkediri') }}
            </a>
          </div>
        </div>
      </div>

      <p class="mt-10 border-t border-outline-green-2 pt-6 text-p-sm text-ink-gray-4">
        {{ t('landing.footer.copyright', { name: brand.name }) }}
      </p>
    </div>
  </footer>
</template>
