<script setup lang="ts">
import { Button } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/features/auth/store'
import { brand } from '@/shared/brand'
import { scrollToId } from '../scroll'
import { useLandingContent } from '../useLandingContent'
import { useStartAction } from '../useStartAction'
import HeroScene from './HeroScene.vue'

const { t } = useI18n()
const auth = useAuthStore()
const { loading, start } = useStartAction()
const { hero } = useLandingContent()

const loopNodes = [
  { key: 'landing.hero.loop.research', color: 'bg-surface-blue-6' },
  { key: 'landing.hero.loop.engineering', color: 'bg-surface-blue-5' },
  { key: 'landing.hero.loop.outreach', color: 'bg-surface-blue-4' },
]

function scrollToFeatures() {
  scrollToId('program')
}

function scrollToPartnership() {
  scrollToId('partnership')
}
</script>

<template>
  <section id="about" class="relative overflow-hidden">
    <div class="absolute inset-0 z-0 opacity-70 md:opacity-100" aria-hidden="true">
      <HeroScene />
      <div
        class="absolute inset-0"
        :style="{
          background:
            'linear-gradient(90deg, var(--surface-base) 0%, color-mix(in srgb, var(--surface-base) 82%, transparent) 34%, transparent 68%)',
        }"
      />
      <div
        class="absolute inset-x-0 bottom-0 h-32"
        :style="{ background: 'linear-gradient(to top, var(--surface-base), transparent)' }"
      />
    </div>

    <div class="relative z-10 mx-auto w-full max-w-6xl px-5 pb-20 pt-20 sm:pt-28">
      <div class="max-w-2xl">
        <span
          class="inline-flex items-center gap-1.5 rounded-full border border-outline-blue-2 bg-surface-blue-1 px-2.5 py-1 text-xs-medium text-ink-blue-7"
        >
            <span class="size-1.5 animate-pulse rounded-full bg-surface-blue-6" />
          {{ hero.badge }}
        </span>

        <p class="mt-4 text-p-sm-medium text-surface-blue-6">
          {{ brand.tagline || t('landing.tagline') }}
        </p>

        <h1 class="mt-6 text-5xl-bold text-ink-gray-9 sm:text-7xl-bold lg:text-10xl-bold">
          {{ hero.title }}
          <span class="text-ink-blue-6">{{ hero.accent }}</span>.
        </h1>

        <p class="mt-5 max-w-xl text-p-lg text-ink-gray-6">
          {{ hero.lead }}
        </p>

        <div class="mt-8 flex flex-wrap items-center gap-3">
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
              :label="t('landing.joinPartner')"
              size="lg"
              variant="solid"
              theme="blue"
              icon-right="lucide-arrow-right"
              @click="scrollToPartnership"
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

        <div class="mt-10 flex flex-wrap gap-2">
          <span
            v-for="node in loopNodes"
            :key="node.key"
            class="inline-flex items-center gap-1.5 rounded-full border border-outline-gray-1 bg-surface-elevation-2 px-2.5 py-1 text-2xs-medium text-ink-gray-6"
          >
            <span class="size-1.5 rounded-full" :class="node.color" />
            {{ t(node.key) }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>
