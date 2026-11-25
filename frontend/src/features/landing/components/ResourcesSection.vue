<script setup lang="ts">
import { Badge, Button } from 'frappe-ui'

import { FLAGSHIP_URL } from '../content'
import { scrollToId } from '../scroll'
import { useLandingContent } from '../useLandingContent'

const { resources } = useLandingContent()

function scrollToContact() {
  scrollToId('contact')
}
</script>

<template>
  <section id="resources" class="border-t border-outline-gray-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="blue" variant="outline" :label="resources.badge" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ resources.title }}</h2>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ resources.lead }}</p>
      </div>

      <div class="mx-auto mt-12 grid max-w-4xl gap-4 md:grid-cols-2">
        <div
          v-for="item in resources.items"
          :key="item.title"
          class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="w-fit rounded-4 bg-surface-blue-1 p-2.5 text-surface-blue-6">
              <span :class="item.icon" class="size-5" aria-hidden="true" />
            </div>
            <span
              class="rounded-full border border-outline-blue-2 px-2.5 py-1 text-2xs-medium text-surface-blue-6"
            >
              {{ item.tag }}
            </span>
          </div>
          <h3 class="mt-5 text-2xl-bold text-ink-gray-9">{{ item.title }}</h3>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ item.desc }}</p>
          <div
            class="mt-5 inline-flex items-center gap-1.5 rounded-full bg-surface-blue-1 px-2.5 py-1 text-2xs-medium text-surface-blue-6"
          >
            <span class="lucide-file-code size-3" aria-hidden="true" />
            {{ item.artifact }}
          </div>
        </div>
      </div>

      <div class="mt-8 flex justify-center">
        <Button
          :label="resources.cta"
          size="lg"
          variant="solid"
          theme="blue"
          icon-right="lucide-arrow-right"
          @click="scrollToContact"
        />
      </div>

      <div
        class="mx-auto mt-10 flex max-w-4xl flex-col items-start justify-between gap-4 rounded-6 border border-outline-blue-2 p-5 sm:flex-row sm:items-center"
        :style="{ background: 'linear-gradient(90deg, var(--surface-blue-1), var(--surface-base))' }"
      >
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="lucide-git-fork size-4 text-ink-blue-7" aria-hidden="true" />
            <a
              :href="FLAGSHIP_URL"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-base-semibold text-ink-gray-8 transition-colors hover:text-ink-blue-7 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
            >
              tantanganbebras
              <span class="lucide-external-link size-3.5" aria-hidden="true" />
            </a>
            <span class="rounded-1 bg-surface-blue-2 px-1.5 py-0.5 text-2xs-medium text-surface-blue-6">
              {{ resources.flagship.status }}
            </span>
          </div>
          <p class="mt-1.5 max-w-2xl text-p-sm text-ink-gray-6">
            {{ resources.flagship.desc }}
          </p>
        </div>
        <span
          class="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-outline-blue-2 bg-surface-base px-2.5 py-1 text-2xs-medium text-surface-blue-6"
        >
          <span class="lucide-scale size-3" aria-hidden="true" />
          {{ resources.flagship.license }}
        </span>
      </div>
    </div>
  </section>
</template>
