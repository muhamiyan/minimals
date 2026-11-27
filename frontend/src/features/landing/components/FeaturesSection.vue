<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { highlights } from '../content'

const { t } = useI18n()

const cards = computed(() =>
  highlights.map((item) => ({
    icon: item.icon,
    title: t(item.title),
    desc: t(item.desc),
  })),
)
</script>

<template>
  <section id="features" class="border-t border-outline-gray-1 bg-surface-base">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="subtle" :label="t('landing.highlights.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
          {{ t('landing.highlights.title') }}
        </h2>
        <p class="mt-3 text-p-base text-ink-gray-6">
          {{ t('landing.highlights.lead') }}
        </p>
      </div>

      <div class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="item in cards"
          :key="item.title"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 p-5 transition-colors hover:border-outline-green-3 hover:bg-surface-green-2"
        >
          <div class="w-fit rounded-4 bg-surface-elevation-2 p-2.5 text-ink-green-7">
            <span :class="item.icon" class="size-5" aria-hidden="true" />
          </div>
          <h3 class="mt-4 text-base-semibold text-ink-gray-8">{{ item.title }}</h3>
          <p class="mt-1.5 text-p-sm text-ink-gray-6">{{ item.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
