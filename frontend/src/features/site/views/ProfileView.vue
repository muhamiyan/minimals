<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { contact } from '@/features/landing/content'

const { t } = useI18n()
</script>

<template>
  <div id="top" class="min-h-screen bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main class="mx-auto w-full max-w-4xl px-5 py-12">
      <header class="mb-10 rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('profile.title') }}</h1>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('profile.lead') }}</p>
      </header>

      <div class="rounded-8 border border-outline-green-2 bg-surface-base p-8">
        <p class="text-p-base leading-relaxed text-ink-gray-7">
          {{ t('profile.about') }}
        </p>
      </div>

      <div class="mt-8 grid gap-4 sm:grid-cols-2">
        <section class="rounded-6 border border-outline-green-2 bg-surface-base p-6">
          <span class="lucide-eye size-5 text-ink-green-6" aria-hidden="true" />
          <h2 class="mt-4 text-xl-semibold text-ink-gray-9">
            {{ t('landing.about.visionLabel') }}
          </h2>
          <p class="mt-3 text-p-sm leading-relaxed text-ink-gray-6">
            {{ t('landing.about.vision') }}
          </p>
        </section>
        <section class="rounded-6 border border-outline-green-2 bg-surface-base p-6">
          <span class="lucide-target size-5 text-ink-green-6" aria-hidden="true" />
          <h2 class="mt-4 text-xl-semibold text-ink-gray-9">
            {{ t('landing.about.missionLabel') }}
          </h2>
          <p class="mt-3 text-p-sm leading-relaxed text-ink-gray-6">
            {{ t('landing.about.mission') }}
          </p>
        </section>
      </div>

      <section class="mt-8 rounded-6 border border-outline-green-2 bg-surface-base p-6">
        <h2 class="text-xl-semibold text-ink-gray-9">{{ t('profile.locationTitle') }}</h2>
        <p class="mt-3 text-p-sm text-ink-gray-6">{{ contact.address }}</p>
      </section>
    </main>
    <LandingFooter />
  </div>
</template>
