<script setup lang="ts">
import { Button } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { PPDB_URL } from '../content'

const { t } = useI18n()
</script>

<template>
  <section id="ppdb" class="mx-auto w-full max-w-6xl px-5 py-20">
    <div
      class="rounded-8 border border-outline-green-3 bg-surface-green-2 px-6 py-16 text-center"
    >
      <div>
        <div class="mx-auto w-fit rounded-6 bg-surface-base p-3 text-ink-green-7">
          <span class="lucide-school size-8" aria-hidden="true" />
        </div>
        <h2 class="mx-auto mt-5 max-w-2xl text-4xl-bold text-ink-gray-9 sm:text-5xl-bold">
          {{ t('landing.ppdb.title') }}
        </h2>
        <p class="mx-auto mt-3 max-w-2xl text-p-base text-ink-gray-6">
          {{ t('landing.ppdb.lead') }}
        </p>
        <p class="mx-auto mt-2 max-w-2xl text-p-sm-medium text-ink-green-7">
          {{ t('landing.ppdb.period') }}
        </p>

        <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button
            :label="t('landing.ppdb.register')"
            :href="PPDB_URL"
            size="lg"
            variant="solid"
            theme="green"
            icon-right="lucide-arrow-up-right"
          />
        </div>
      </div>
    </div>
  </section>
</template>
