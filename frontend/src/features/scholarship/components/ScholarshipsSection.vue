<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useScholarshipStore } from '../store'

const { t } = useI18n()
const scholarships = useScholarshipStore()
</script>

<template>
  <section
    v-if="scholarships.scholarships.length"
    id="scholarship"
    class="border-t border-outline-green-2 bg-surface-base"
  >
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="mx-auto max-w-2xl text-center">
        <Badge theme="green" variant="outline" :label="t('landing.scholarship.badge')" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
          {{ t('landing.scholarship.title') }}
        </h2>
        <p class="mt-3 text-p-base text-ink-gray-6">
          {{ t('landing.scholarship.lead') }}
        </p>
      </div>

      <div class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="item in scholarships.scholarships"
          :key="item.id"
          :to="{ name: 'ScholarshipPost', params: { slug: item.slug } }"
          class="group flex flex-col overflow-hidden rounded-6 border border-outline-green-2 bg-surface-base transition-colors hover:border-outline-green-3"
        >
          <img
            v-if="item.coverImage"
            :src="item.coverImage"
            alt=""
            class="aspect-[16/9] w-full object-cover"
          />
          <div
            v-else
            class="flex aspect-[16/9] w-full items-center justify-center bg-surface-green-1 text-ink-green-7"
          >
            <span class="lucide-award size-8" aria-hidden="true" />
          </div>
          <div class="flex flex-1 flex-col p-5">
            <p class="text-2xs-medium uppercase tracking-wide text-ink-green-7">
              {{ item.level }}
            </p>
            <h3 class="mt-2 text-lg-semibold leading-snug text-ink-gray-8 group-hover:text-ink-gray-9">
              {{ item.title }}
            </h3>
            <p class="mt-2 flex-1 text-p-sm text-ink-gray-6">{{ item.excerpt }}</p>
            <span class="mt-4 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7">
              {{ t('scholarship.list.readMore') }}
              <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
            </span>
          </div>
        </router-link>
      </div>
    </div>
  </section>
</template>
