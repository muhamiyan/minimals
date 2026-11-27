<script setup lang="ts">
import { contentValue } from '@/shared/siteContent'
import { Badge } from 'frappe-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { contact, MAPS_EMBED_URL, MAPS_LINK_URL } from '../content'

const { t } = useI18n()

const cards = computed(() => {
  const email = contentValue('contact.email', contact.email)
  return [
    {
      icon: 'lucide-map-pin',
      label: 'landing.contact.addressLabel',
      value: contentValue('contact.address', contact.address),
      href: '',
      external: false,
    },
    {
      icon: 'lucide-mail',
      label: 'landing.contact.emailLabel',
      value: email,
      href: `mailto:${email}`,
      external: false,
    },
    {
      icon: 'lucide-message-circle',
      label: 'landing.contact.whatsappLabel',
      value: contentValue('contact.whatsappDisplay', '0878 6470 6565'),
      href: contentValue('contact.whatsappUrl', contact.whatsapp),
      external: true,
    },
    {
      icon: 'lucide-facebook',
      label: 'landing.contact.facebookLabel',
      value: contentValue('contact.facebookDisplay', 'manw.selaparangkediri'),
      href: contentValue('contact.facebookUrl', contact.facebook),
      external: true,
    },
  ]
})
</script>

<template>
  <section id="contact" class="border-t border-outline-gray-1 bg-surface-base">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="subtle" :label="t('landing.contact.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ t('landing.contact.title') }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('landing.contact.lead') }}</p>
      </div>

      <div class="mx-auto mt-12 grid max-w-4xl gap-4 sm:grid-cols-2">
        <div
          v-for="item in cards"
          :key="item.label"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 p-5"
        >
          <div class="w-fit rounded-4 bg-surface-elevation-2 p-2 text-ink-green-7">
            <span :class="item.icon" class="size-5" aria-hidden="true" />
          </div>
          <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
            {{ t(item.label) }}
          </p>
          <a
            v-if="item.href"
            :href="item.href"
            :target="item.external ? '_blank' : undefined"
            :rel="item.external ? 'noopener noreferrer' : undefined"
            class="mt-1 block break-all text-p-sm text-ink-green-7 hover:underline"
          >
            {{ item.value }}
          </a>
          <p v-else class="mt-1 text-p-sm text-ink-gray-8">{{ item.value }}</p>
        </div>
      </div>

      <div class="mx-auto mt-10 max-w-3xl">
        <h3 class="mb-3 text-base-semibold text-ink-gray-8">
          {{ t('landing.contact.mapTitle') }}
        </h3>
        <div class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2">
          <iframe
            :src="contentValue('contact.mapsUrl', MAPS_EMBED_URL)"
            :title="t('landing.contact.mapTitle')"
            class="h-52 w-full border-0 sm:h-64"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen
          />
        </div>
        <a
          :href="MAPS_LINK_URL"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-3 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7 hover:underline"
        >
          {{ t('landing.contact.openMap') }}
          <span class="lucide-arrow-up-right size-3.5" aria-hidden="true" />
        </a>
      </div>
    </div>
  </section>
</template>
