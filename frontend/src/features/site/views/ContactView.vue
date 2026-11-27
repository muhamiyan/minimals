<script setup lang="ts">
import { Button, ErrorMessage, FormControl, Textarea } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { contact, MAPS_EMBED_URL, MAPS_LINK_URL } from '@/features/landing/content'
import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { contentValue } from '@/shared/siteContent'

import { useContactStore } from '../store'

const { t } = useI18n()
const store = useContactStore()

const form = reactive({ name: '', phone: '', email: '', message: '' })
const justSent = ref(false)

watch(
  form,
  () => {
    if (!justSent.value) store.reset()
  },
  { flush: 'sync' },
)

async function onSubmit() {
  const ok = await store.sendMessage({
    name: form.name.trim(),
    phone: form.phone.trim(),
    email: form.email.trim() || undefined,
    message: form.message.trim(),
  })
  if (ok) {
    justSent.value = true
    form.name = ''
    form.phone = ''
    form.email = ''
    form.message = ''
    justSent.value = false
  }
}
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main class="mx-auto w-full max-w-5xl px-5 py-12">
      <header class="mb-10 max-w-2xl rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('contactPage.title') }}</h1>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('contactPage.lead') }}</p>
      </header>

      <div class="grid gap-8 md:grid-cols-2">
        <form class="space-y-4" @submit.prevent="onSubmit">
          <FormControl
            v-model="form.name"
            :label="t('contactPage.form.name')"
            :placeholder="t('contactPage.form.namePlaceholder')"
            required
          />
          <FormControl
            v-model="form.phone"
            :label="t('contactPage.form.phone')"
            :placeholder="t('contactPage.form.phonePlaceholder')"
            required
          />
          <FormControl
            v-model="form.email"
            type="email"
            :label="t('contactPage.form.email')"
            :placeholder="t('contactPage.form.emailPlaceholder')"
          />
          <div>
            <div class="mb-1.5 text-base-medium text-ink-gray-7">
              {{ t('contactPage.form.message') }}
            </div>
            <Textarea
              v-model="form.message"
              :placeholder="t('contactPage.form.messagePlaceholder')"
              :rows="5"
            />
          </div>

          <ErrorMessage v-if="store.error" :message="store.error" />
          <p v-if="store.sent" class="text-p-sm-medium text-ink-green-7">
            {{ t('contactPage.success') }}
          </p>

          <Button
            type="submit"
            :label="t('contactPage.form.submit')"
            variant="solid"
            theme="green"
            icon-left="lucide-send"
            :loading="store.sending"
          />
        </form>

        <aside class="space-y-4">
          <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
            <span class="lucide-map-pin size-5 text-ink-green-6" aria-hidden="true" />
            <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
              {{ t('landing.contact.addressLabel') }}
            </p>
            <p class="mt-1 text-p-sm text-ink-gray-8">
              {{ contentValue('contact.address', contact.address) }}
            </p>
          </div>
          <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
            <span class="lucide-mail size-5 text-ink-green-6" aria-hidden="true" />
            <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
              {{ t('landing.contact.emailLabel') }}
            </p>
            <a
              :href="`mailto:${contentValue('contact.email', contact.email)}`"
              class="mt-1 block break-all text-p-sm text-ink-green-7"
            >
              {{ contentValue('contact.email', contact.email) }}
            </a>
          </div>
          <a
            :href="contentValue('contact.whatsappUrl', contact.whatsapp)"
            target="_blank"
            rel="noopener noreferrer"
            class="block rounded-6 border border-outline-green-2 bg-surface-base p-5 transition-colors hover:border-outline-green-3"
          >
            <span class="lucide-message-circle size-5 text-ink-green-6" aria-hidden="true" />
            <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
              {{ t('landing.contact.whatsappLabel') }}
            </p>
            <p class="mt-1 text-p-sm text-ink-gray-8">
              {{ contentValue('contact.whatsappDisplay', '0878 6470 6565') }}
            </p>
          </a>
        </aside>
      </div>

      <section class="mt-12">
        <h2 class="mb-3 text-xl-semibold text-ink-gray-8">
          {{ t('contactPage.mapTitle') }}
        </h2>
        <div class="overflow-hidden rounded-6 border border-outline-green-2 bg-surface-base">
          <iframe
            :src="contentValue('contact.mapsUrl', MAPS_EMBED_URL)"
            :title="t('contactPage.mapTitle')"
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
          {{ t('contactPage.openMap') }}
          <span class="lucide-arrow-up-right size-3.5" aria-hidden="true" />
        </a>
      </section>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>
