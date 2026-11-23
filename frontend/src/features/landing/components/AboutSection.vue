<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { principles } from '../content'

const { t } = useI18n()
</script>

<template>
  <section id="about" class="border-t border-outline-gray-1">
    <div class="mx-auto grid w-full max-w-6xl gap-10 px-5 py-20 lg:grid-cols-5">
      <div class="lg:col-span-3">
        <Badge theme="blue" variant="outline" :label="t('landing.about.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ t('landing.about.title') }}</h2>
        <div class="mt-5 max-w-xl space-y-4 text-p-base text-ink-gray-6">
          <p>{{ t('landing.about.body1') }}</p>
          <p>{{ t('landing.about.body2') }}</p>
        </div>
      </div>

      <div class="lg:col-span-2">
        <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <div class="flex items-center gap-2 text-base-semibold text-ink-gray-8">
            <span class="lucide-badge-check size-4 text-ink-blue-7" aria-hidden="true" />
            {{ t('landing.about.rules') }}
          </div>
          <ul class="mt-4 space-y-3">
            <li
              v-for="rule in principles"
              :key="rule"
              class="flex gap-2.5 text-p-sm text-ink-gray-6"
            >
              <span
                class="lucide-check mt-0.5 size-4 shrink-0 text-ink-green-6"
                aria-hidden="true"
              />
              <span>{{ t(rule) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>
