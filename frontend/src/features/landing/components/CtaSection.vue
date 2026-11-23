<script setup lang="ts">
import { Button } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/features/auth/store'
import { useStartAction } from '../useStartAction'

const { t } = useI18n()
const auth = useAuthStore()
const { loading, start } = useStartAction()

function scrollToFeatures() {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <section class="mx-auto w-full max-w-6xl px-5 pb-20">
    <div
      class="relative overflow-hidden rounded-8 border border-outline-gray-1 bg-surface-elevation-2 px-6 py-16 text-center"
    >
      <div
        aria-hidden="true"
        class="pointer-events-none absolute -right-24 -top-24 size-72 rounded-full bg-surface-blue-4 opacity-30 blur-3xl"
      />
      <div
        aria-hidden="true"
        class="pointer-events-none absolute -bottom-28 -left-20 size-64 rounded-full bg-surface-violet-4 opacity-30 blur-3xl"
      />

      <div class="relative">
        <h2 class="mx-auto max-w-2xl text-4xl-bold text-ink-gray-9 sm:text-5xl-bold">
          {{ t('landing.cta.title') }}
        </h2>
        <p class="mx-auto mt-3 max-w-xl text-p-base text-ink-gray-6">
          {{ t('landing.cta.lead') }}
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
            :route="{ name: 'Login' }"
          />
          <Button
            v-else
            :label="t('landing.whatsInside')"
            size="lg"
            variant="outline"
            @click="scrollToFeatures"
          />
        </div>
      </div>
    </div>
  </section>
</template>
