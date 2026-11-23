<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <section id="scholarship" class="border-t border-outline-green-2 bg-surface-green-2">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto flex max-w-3xl flex-col items-center gap-10 text-center">
        <div>
          <Badge theme="green" variant="outline" :label="t('landing.support.badge')" />
          <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
            {{ t('landing.support.title') }}
          </h2>
          <p class="mx-auto mt-4 max-w-xl text-p-base leading-relaxed text-ink-gray-6">
            {{ t('landing.support.lead') }}
          </p>
          <p class="mx-auto mt-3 max-w-xl text-p-sm leading-relaxed text-ink-gray-6">
            {{ t('landing.support.body') }}
          </p>
        </div>

        <div class="w-full max-w-xl rounded-8 border border-outline-green-2 bg-surface-base p-8 text-center">
          <div class="mx-auto w-fit rounded-6 bg-surface-green-3 p-3 text-ink-green-8">
            <span class="lucide-hand-heart size-8" aria-hidden="true" />
          </div>
          <p class="mt-5 text-p-base text-ink-gray-7">{{ t('landing.support.note') }}</p>
          <a
            href="#contact"
            class="mx-auto mt-6 inline-flex items-center gap-2 text-p-sm-medium text-ink-green-7"
          >
            {{ t('landing.support.contact') }}
            <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
          </a>
        </div>
      </div>
    </div>
  </section>
</template>
