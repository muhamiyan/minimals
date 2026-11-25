<script setup lang="ts">
import { Badge } from 'frappe-ui'

import { useLandingContent } from '../useLandingContent'

const { partnership } = useLandingContent()
</script>

<template>
  <section id="partnership" class="border-t border-outline-gray-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="partnership.badge" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ partnership.title }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ partnership.lead }}</p>
      </div>

      <div class="mt-12 grid gap-4 lg:grid-cols-2">
        <div
          v-for="program in partnership.programs"
          :key="program.title"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-blue-4 bg-surface-elevation-2 p-6"
        >
          <div class="flex flex-wrap items-center gap-3">
            <div class="w-fit rounded-4 bg-surface-blue-1 p-2.5 text-surface-blue-6">
              <span :class="program.icon" class="size-5" aria-hidden="true" />
            </div>
            <span
              class="rounded-full border border-outline-blue-2 px-2.5 py-1 text-2xs-medium text-surface-blue-6"
            >
              {{ program.tag }}
            </span>
          </div>
          <h3 class="mt-5 text-2xl-bold text-ink-gray-9">{{ program.title }}</h3>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ program.desc }}</p>
          <ul class="mt-5 space-y-3">
            <li
              v-for="item in program.items"
              :key="item"
              class="flex gap-2.5 text-p-sm text-ink-gray-6"
            >
              <span
                class="lucide-check mt-0.5 size-4 shrink-0 text-surface-blue-6"
                aria-hidden="true"
              />
              <span>{{ item }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>
