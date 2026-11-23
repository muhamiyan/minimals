<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { features } from '../content'

const { t } = useI18n()
</script>

<template>
  <section id="features" class="border-t border-outline-gray-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="t('landing.features.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
          {{ t('landing.features.title') }}
        </h2>
        <p class="mt-3 text-p-base text-ink-gray-6">
          {{ t('landing.features.lead') }}
        </p>
      </div>

      <div class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="(feature, i) in features"
          :key="feature.title"
          class="group relative rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-blue-3 hover:bg-surface-elevation-3"
        >
          <span class="absolute right-4 top-4 text-2xs-medium text-ink-gray-4">
            {{ String(i + 1).padStart(2, '0') }}
          </span>
          <div
            class="w-fit rounded-4 bg-surface-gray-2 p-2.5 text-ink-gray-6 transition-colors group-hover:text-ink-blue-7"
          >
            <span :class="feature.icon" class="size-5" aria-hidden="true" />
          </div>
          <h3 class="mt-4 text-base-semibold text-ink-gray-8">
            {{ t(feature.title) }}
          </h3>
          <p class="mt-1.5 text-p-sm text-ink-gray-6">{{ t(feature.desc) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
