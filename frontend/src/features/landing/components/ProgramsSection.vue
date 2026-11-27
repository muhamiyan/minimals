<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useProgramStore } from '@/features/program/store'

const { t } = useI18n()
const programs = useProgramStore()
</script>

<template>
  <section
    v-if="programs.programs.length"
    id="programs"
    class="border-t border-outline-gray-1 bg-surface-base"
  >
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="subtle" :label="t('landing.programs.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ t('landing.programs.title') }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('landing.programs.lead') }}</p>
      </div>

      <div class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="item in programs.programs"
          :key="item.id"
          :to="{ name: 'ProgramPost', params: { slug: item.slug } }"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 p-5 transition-colors hover:border-outline-green-3 hover:bg-surface-green-2"
        >
          <div class="w-fit rounded-4 bg-surface-elevation-2 p-2 text-ink-green-7">
            <span class="lucide-graduation-cap size-5" aria-hidden="true" />
          </div>
          <p class="mt-4 text-2xs-medium uppercase tracking-wide text-ink-green-7">
            {{ item.level }}
          </p>
          <h3 class="mt-1 text-base-semibold leading-snug text-ink-gray-8">
            {{ item.title }}
          </h3>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ item.excerpt }}</p>
        </router-link>
      </div>

      <div class="mt-8 text-center">
        <router-link
          :to="{ name: 'ProgramList' }"
          class="inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
        >
          {{ t('program.list.readMore') }}
          <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
        </router-link>
      </div>
    </div>
  </section>
</template>
