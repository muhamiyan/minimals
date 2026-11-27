<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useProgramStore } from '@/features/program/store'
import { useScholarshipStore } from '@/features/scholarship/store'
import { contentValue } from '@/shared/siteContent'

import { principles, stats } from '../content'

const { t } = useI18n()
const program = useProgramStore()
const scholarship = useScholarshipStore()

const principleItems = computed(() => principles.map((rule) => t(rule)))

const statItems = computed(() => {
  const values = [
    String(program.total || program.programs.length),
    contentValue('contact.studentCount', stats[1].value),
    contentValue('contact.staffCount', stats[2].value),
    String(scholarship.total || scholarship.scholarships.length),
  ]
  return stats.map((item, index) => ({
    icon: item.icon,
    value: values[index],
    label: t(item.label),
  }))
})
</script>

<template>
  <section id="about" class="border-t border-outline-gray-1 bg-surface-base">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="subtle" :label="t('landing.about.badge')" />
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
                <span v-html="t('landing.about.vision')" />
              </p>
            </div>
            <div>
              <h3 class="text-base-semibold text-ink-gray-8">
                {{ t('landing.about.missionLabel') }}
              </h3>
              <p class="mt-2 text-p-base leading-relaxed text-ink-gray-6">
                <span v-html="t('landing.about.mission')" />
              </p>
            </div>
            <p class="text-p-sm leading-relaxed text-ink-gray-6">
              <span v-html="t('landing.about.body')" />
            </p>
          </div>
        </div>

        <div class="lg:col-span-2">
          <div class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 p-5">
            <div class="flex items-center gap-2 text-base-semibold text-ink-gray-8">
              <span class="lucide-badge-check size-4 text-ink-green-7" aria-hidden="true" />
              {{ t('landing.about.rules') }}
            </div>
            <ul class="mt-4 space-y-3">
              <li
                v-for="rule in principleItems"
                :key="rule"
                class="flex gap-2.5 text-p-sm text-ink-gray-6"
              >
                <span
                  class="lucide-check mt-0.5 size-4 shrink-0 text-ink-green-7"
                  aria-hidden="true"
                />
                <span>{{ rule }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="mt-12 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="stat in statItems"
          :key="stat.label"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 p-5 text-center"
        >
          <div class="mx-auto w-fit rounded-4 bg-surface-elevation-2 p-2 text-ink-green-7">
            <span :class="stat.icon" class="size-5" aria-hidden="true" />
          </div>
          <p class="mt-3 text-4xl-bold text-ink-green-7">{{ stat.value }}</p>
          <p class="mt-1 text-p-sm text-ink-gray-6">{{ stat.label }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
