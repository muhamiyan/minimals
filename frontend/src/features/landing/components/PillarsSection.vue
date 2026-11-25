<script setup lang="ts">
import { Badge } from 'frappe-ui'

import { useLandingContent } from '../useLandingContent'

const { pillars } = useLandingContent()
</script>

<template>
  <section id="program" class="border-t border-outline-gray-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="pillars.badge" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ pillars.title }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ pillars.lead }}</p>
      </div>

      <div class="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="pillar in pillars.items"
          :key="pillar.code"
          class="group flex flex-col rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-blue-3 hover:bg-surface-elevation-3"
        >
          <div class="flex items-start justify-between">
            <div class="w-fit rounded-4 bg-surface-blue-1 p-2.5 text-surface-blue-6">
              <span :class="pillar.icon" class="size-5" aria-hidden="true" />
            </div>
            <span class="text-2xs-medium text-surface-blue-5">{{ pillar.code }}</span>
          </div>
          <h3 class="mt-4 text-base-semibold text-ink-gray-8">{{ pillar.title }}</h3>
          <p class="mt-1.5 text-p-sm text-ink-gray-6">{{ pillar.desc }}</p>
          <div class="mt-auto pt-4">
            <span
              class="inline-flex items-center gap-1.5 rounded-full bg-surface-blue-1 px-2.5 py-1 text-2xs-medium text-surface-blue-6"
            >
              <span class="lucide-file-code size-3" aria-hidden="true" />
              {{ pillar.artifact }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
