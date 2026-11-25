<script setup lang="ts">
import { Badge } from 'frappe-ui'

import { useLandingContent } from '../useLandingContent'

const { contact } = useLandingContent()
</script>

<template>
  <section id="contact" class="border-t border-outline-gray-1 bg-surface-elevation-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="contact.badge" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ contact.title }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ contact.lead }}</p>
      </div>

      <div class="mx-auto mt-12 grid max-w-4xl gap-4 sm:grid-cols-3">
        <div
          v-for="entry in contact.entries"
          :key="entry.label"
          class="rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-blue-4 bg-surface-elevation-2 p-5"
        >
          <span :class="entry.icon" class="size-5 text-surface-blue-6" aria-hidden="true" />
          <div class="mt-4 text-xs-medium text-ink-gray-5">{{ entry.label }}</div>
          <a
            v-if="entry.href"
            :href="entry.href"
            class="mt-1 block break-words text-p-sm-medium text-ink-gray-8 transition-colors hover:text-ink-blue-7 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
            :target="entry.href.startsWith('http') ? '_blank' : undefined"
            rel="noopener noreferrer"
          >
            {{ entry.value }}
          </a>
          <div v-else class="mt-1 text-p-sm-medium text-ink-gray-8">{{ entry.value }}</div>
          <div v-if="entry.note" class="mt-0.5 text-2xs-medium text-ink-gray-4">
            {{ entry.note }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
