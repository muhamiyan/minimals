<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { facilities } from '../content'

const { t } = useI18n()
</script>

<template>
  <section id="facilities" class="border-t border-outline-green-2 bg-surface-green-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="outline" :label="t('landing.facilities.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
          {{ t('landing.facilities.title') }}
        </h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('landing.facilities.lead') }}</p>
      </div>

      <div class="mt-12 grid gap-4 md:grid-cols-3">
        <article
          v-for="item in facilities"
          :key="item.title"
          class="rounded-6 border border-outline-green-2 bg-surface-base p-5 transition-colors hover:border-outline-green-3"
        >
          <div class="w-fit rounded-4 bg-surface-green-2 p-2.5 text-ink-green-7">
            <span :class="item.icon" class="size-5" aria-hidden="true" />
          </div>
          <h3 class="mt-4 text-base-semibold text-ink-gray-8">{{ t(item.title) }}</h3>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ t(item.desc) }}</p>
        </article>
      </div>
    </div>
  </section>
</template>
