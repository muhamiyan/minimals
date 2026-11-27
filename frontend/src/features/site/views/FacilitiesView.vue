<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import { facilities } from '@/features/landing/content'
import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'

const { t } = useI18n()

const cards = facilities.map((item) => ({
  icon: item.icon,
  title: item.title,
  desc: item.desc,
}))
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main class="mx-auto w-full max-w-4xl px-5 py-12">
      <header class="mb-10 rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('facilitiesPage.title') }}</h1>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('facilitiesPage.lead') }}</p>
      </header>

      <div class="grid gap-4 sm:grid-cols-2">
        <section
          v-for="item in cards"
          :key="item.title"
          class="rounded-6 border border-outline-green-2 bg-surface-base p-6"
        >
          <span :class="item.icon" class="size-6 text-ink-green-6" aria-hidden="true" />
          <h2 class="mt-4 text-xl-semibold text-ink-gray-9">{{ t(item.title) }}</h2>
          <p class="mt-3 text-p-sm leading-relaxed text-ink-gray-6">{{ t(item.desc) }}</p>
        </section>
      </div>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>
