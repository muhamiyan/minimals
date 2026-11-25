<script setup lang="ts">
import { Badge } from 'frappe-ui'

import { useLandingContent } from '../useLandingContent'

const { loop } = useLandingContent()

const tones = ['text-surface-blue-6', 'text-surface-blue-5', 'text-surface-blue-4']
</script>

<template>
  <section id="loop" class="border-t border-outline-gray-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="loop.badge" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ loop.title }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ loop.lead }}</p>
      </div>

      <div class="mt-12 flex flex-col gap-4 md:flex-row md:items-stretch">
        <template v-for="(step, i) in loop.steps" :key="step.title">
          <div class="relative flex-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
            <span class="absolute right-4 top-4 text-2xs-medium" :class="tones[i]">
              {{ String(i + 1).padStart(2, '0') }}
            </span>
            <span :class="[step.icon, tones[i]]" class="size-5" aria-hidden="true" />
            <h3 class="mt-4 text-base-semibold text-ink-gray-8">{{ step.title }}</h3>
            <p class="mt-1.5 text-p-sm text-ink-gray-6">{{ step.desc }}</p>
          </div>
          <div
            v-if="i < loop.steps.length - 1"
            class="hidden shrink-0 items-center justify-center px-1 md:flex"
            aria-hidden="true"
          >
            <span class="lucide-arrow-right size-5 text-surface-blue-4" />
          </div>
        </template>
      </div>

      <div class="mt-6 flex justify-center">
        <span
          class="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-p-sm"
          :style="{
            borderColor: 'color-mix(in srgb, var(--surface-blue-6) 35%, transparent)',
            background: 'color-mix(in srgb, var(--surface-blue-6) 8%, var(--surface-base))',
            color: 'var(--surface-blue-6)',
          }"
        >
          <span class="lucide-refresh-cw size-3.5" aria-hidden="true" />
          {{ loop.return }}
        </span>
      </div>
    </div>
  </section>
</template>
