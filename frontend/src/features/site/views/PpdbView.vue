<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Button } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { PPDB_URL } from '@/features/landing/content'
import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { useProgramStore } from '@/features/program/store'

const { t } = useI18n()
const programs = useProgramStore()

const gateReady = computed(() => programs.checked)

onMounted(async () => {
  if (!programs.checked) await programs.fetchList()
})
</script>

<template>
  <div id="top" class="min-h-screen bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-4xl px-5 py-12">
      <header class="mb-10 max-w-2xl rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('ppdbPage.title') }}</h1>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('ppdbPage.lead') }}</p>
      </header>

      <div class="grid gap-4 sm:grid-cols-3">
        <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
          <span class="lucide-calendar-days size-5 text-ink-green-6" aria-hidden="true" />
          <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
            {{ t('landing.hero.periodLabel') }}
          </p>
          <p class="mt-1 text-base-semibold text-ink-gray-8">
            {{ t('landing.hero.period') }}
          </p>
        </div>
        <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
          <span class="lucide-clock size-5 text-ink-green-6" aria-hidden="true" />
          <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
            {{ t('landing.hero.hoursLabel') }}
          </p>
          <p class="mt-1 text-base-semibold text-ink-gray-8">
            {{ t('landing.hero.hours') }}
          </p>
        </div>
        <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
          <span class="lucide-map-pin size-5 text-ink-green-6" aria-hidden="true" />
          <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-5">
            {{ t('landing.hero.locationLabel') }}
          </p>
          <p class="mt-1 text-base-semibold text-ink-gray-8">
            {{ t('landing.hero.location') }}
          </p>
        </div>
      </div>

      <section class="mt-10 rounded-8 border border-outline-green-2 bg-surface-base p-8 text-center">
        <span class="lucide-file-check-2 mx-auto size-8 text-ink-green-6" aria-hidden="true" />
        <h2 class="mt-5 text-2xl-semibold text-ink-gray-9">{{ t('ppdbPage.formTitle') }}</h2>
        <p class="mx-auto mt-3 max-w-xl text-p-sm text-ink-gray-6">
          {{ t('ppdbPage.formLead') }}
        </p>
        <Button
          class="mt-6"
          :label="t('landing.ppdb.register')"
          :href="PPDB_URL"
          variant="solid"
          theme="green"
          size="lg"
          icon-right="lucide-arrow-up-right"
        />
      </section>

      <section class="mt-10">
        <h2 class="text-xl-semibold text-ink-gray-9">{{ t('ppdbPage.programsTitle') }}</h2>
        <ul class="mt-4 space-y-2">
          <li
            v-for="item in programs.programs"
            :key="item.id"
            class="flex items-center gap-3 rounded-6 border border-outline-green-2 bg-surface-base px-4 py-3"
          >
            <span class="lucide-check size-4 shrink-0 text-ink-green-7" aria-hidden="true" />
            <span class="text-p-sm text-ink-gray-8">{{ item.title }}</span>
          </li>
        </ul>
      </section>
    </main>
    <LandingFooter />
  </div>
</template>
