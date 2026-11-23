<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { principles, stats } from '../content'

const { t } = useI18n()
</script>

<template>
  <section id="about" class="border-t border-outline-green-2 bg-surface-green-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="outline" :label="t('landing.about.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ t('landing.about.title') }}</h2>
      </div>

      <div class="mt-12 grid gap-10 lg:grid-cols-5">
        <div class="lg:col-span-3">
          <div class="space-y-6">
            <div>
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ t('landing.about.visionLabel') }}
              </h3>
              <p class="mt-2 text-p-base leading-relaxed text-ink-gray-6">
                {{ t('landing.about.vision') }}
              </p>
            </div>
            <div>
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ t('landing.about.missionLabel') }}
              </h3>
              <p class="mt-2 text-p-base leading-relaxed text-ink-gray-6">
                {{ t('landing.about.mission') }}
              </p>
            </div>
            <p class="text-p-sm leading-relaxed text-ink-gray-6">
              {{ t('landing.about.body') }}
            </p>
          </div>
        </div>

        <div class="lg:col-span-2">
          <div class="rounded-6 border border-outline-green-2 bg-surface-base p-5">
            <div class="flex items-center gap-2 text-base-semibold text-ink-gray-8">
              <span class="lucide-badge-check size-4 text-ink-green-7" aria-hidden="true" />
              {{ t('landing.about.rules') }}
            </div>
            <ul class="mt-4 space-y-3">
              <li
                v-for="rule in principles"
                :key="rule"
                class="flex gap-2.5 text-p-sm text-ink-gray-6"
              >
                <span
                  class="lucide-check mt-0.5 size-4 shrink-0 text-ink-green-7"
                  aria-hidden="true"
                />
                <span>{{ t(rule) }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="rounded-6 border border-outline-green-2 bg-surface-base p-5 text-center"
        >
          <div class="mx-auto w-fit rounded-4 bg-surface-green-2 p-2 text-ink-green-7">
            <span :class="stat.icon" class="size-5" aria-hidden="true" />
          </div>
          <p class="mt-3 text-4xl-bold text-ink-green-7">{{ stat.value }}</p>
          <p class="mt-1 text-p-sm text-ink-gray-6">{{ t(stat.label) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
