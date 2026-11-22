<script setup lang="ts">
import { Button } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/features/auth/store'
import { pipeline, stack } from '../content'
import { useStartAction } from '../useStartAction'

const { t } = useI18n()
const auth = useAuthStore()
const { loading, start } = useStartAction()

function scrollToFeatures() {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <section class="relative overflow-hidden">
    <div
      aria-hidden="true"
      class="pointer-events-none absolute -top-32 left-1/2 h-80 w-128 -translate-x-1/2 rounded-full bg-surface-blue-4 opacity-40 blur-3xl"
    />

    <div class="relative mx-auto w-full max-w-6xl px-5 pb-16 pt-16 text-center sm:pt-24">
      <span
        class="inline-flex items-center gap-1.5 rounded-full border border-outline-blue-2 bg-surface-blue-1 px-2.5 py-1 text-xs-medium text-ink-blue-7"
      >
        <span class="size-1.5 animate-pulse rounded-full bg-surface-green-7" />
        {{ t('landing.hero.badge') }}
      </span>

      <h1 class="mx-auto mt-6 max-w-3xl text-7xl-bold text-ink-gray-9 sm:text-10xl-bold">
        {{ t('landing.hero.title') }}
        <span class="text-ink-blue-6">{{ t('landing.hero.accent') }}</span>.
      </h1>

      <p class="mx-auto mt-5 max-w-2xl text-p-lg text-ink-gray-6">
        {{ t('landing.hero.lead') }}
      </p>

      <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button
          v-if="!auth.user"
          :label="t('landing.getStarted')"
          size="lg"
          variant="solid"
          theme="blue"
          icon-right="lucide-arrow-right"
          :loading="loading"
          @click="start"
        />
        <Button
          v-else
          :label="t('landing.openDashboard')"
          size="lg"
          variant="solid"
          theme="blue"
          icon-right="lucide-arrow-right"
          :loading="loading"
          @click="start"
        />
        <Button
          v-if="!auth.user"
          :label="t('auth.signIn')"
          size="lg"
          variant="outline"
          icon-left="lucide-log-in"
          :route="{ name: 'Login' }"
        />
        <Button
          v-else
          :label="t('landing.whatsInside')"
          size="lg"
          variant="outline"
          icon-left="lucide-sparkles"
          @click="scrollToFeatures"
        />
      </div>

      <div class="relative mx-auto mt-14 w-full max-w-2xl">
        <div
          class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2 text-left shadow-lg"
        >
          <div
            class="flex items-center gap-1.5 border-b border-outline-gray-1 bg-surface-elevation-1 px-4 py-2.5"
          >
            <span class="size-2.5 rounded-full bg-surface-red-4" />
            <span class="size-2.5 rounded-full bg-surface-amber-4" />
            <span class="size-2.5 rounded-full bg-surface-green-4" />
            <span class="ml-2 text-xs-medium text-ink-gray-5">
              {{ t('landing.hero.lifecycle') }}
            </span>
            <span
              class="ml-auto rounded-1 bg-surface-green-2 px-1.5 py-0.5 text-2xs-medium text-ink-green-8"
            >
              {{ t('landing.hero.ok') }}
            </span>
          </div>

          <div class="space-y-3 p-4 font-mono text-xs">
            <div class="flex items-center gap-2">
              <span
                class="rounded-1 bg-surface-blue-2 px-1.5 py-0.5 text-2xs-medium text-ink-blue-7"
              >
                POST
              </span>
              <span class="text-ink-gray-6">/api/v1/auth/login</span>
            </div>

            <div
              class="flex flex-wrap items-center gap-1.5 rounded-4 border border-outline-gray-1 bg-surface-base p-2.5"
            >
              <template v-for="(layer, i) in pipeline" :key="layer">
                <span
                  class="rounded-1 bg-surface-gray-2 px-1.5 py-0.5 text-2xs-medium text-ink-gray-7"
                >
                  {{ layer }}
                </span>
                <span
                  v-if="i < pipeline.length - 1"
                  class="lucide-chevron-right size-3 text-ink-gray-4"
                  aria-hidden="true"
                />
              </template>
            </div>

            <div class="text-p-xs leading-relaxed">
              <div class="text-ink-gray-4">{</div>
              <div class="pl-4">
                <span class="text-ink-blue-7">"email"</span>
                <span class="text-ink-gray-4">: </span>
                <span class="text-ink-green-7">"admin@minimals.app"</span>
                <span class="text-ink-gray-4">,</span>
              </div>
              <div class="pl-4">
                <span class="text-ink-blue-7">"appRole"</span>
                <span class="text-ink-gray-4">: </span>
                <span class="text-ink-green-7">"admin"</span>
                <span class="text-ink-gray-4">,</span>
              </div>
              <div class="pl-4">
                <span class="text-ink-blue-7">"roles"</span>
                <span class="text-ink-gray-4">: [</span>
                <span class="text-ink-green-7">"Member"</span>
                <span class="text-ink-gray-4">]</span>
              </div>
              <div class="text-ink-gray-4">}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-14 flex flex-wrap items-center justify-center gap-2">
        <span
          v-for="item in stack"
          :key="item"
          class="rounded-full border border-outline-gray-1 bg-surface-elevation-1 px-3 py-1 text-xs-medium text-ink-gray-5"
        >
          {{ item }}
        </span>
      </div>
    </div>
  </section>
</template>
