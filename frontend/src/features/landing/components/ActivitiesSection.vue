<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useActivityStore } from '@/features/activity/store'
import { formatDate } from '@/shared/format'

const { t } = useI18n()
const activities = useActivityStore()
</script>

<template>
  <section id="activities" class="border-t border-outline-green-2 bg-surface-green-1">
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div class="max-w-2xl">
          <Badge theme="green" variant="outline" :label="t('activity.badge')" />
          <h2 class="mt-4 text-5xl-bold text-ink-gray-9">
            {{ t('activity.title') }}
          </h2>
          <p class="mt-3 text-p-base text-ink-gray-6">{{ t('activity.lead') }}</p>
        </div>
        <router-link
          :to="{ name: 'ActivityList' }"
          class="inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
        >
          {{ t('activity.all') }}
          <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
        </router-link>
      </div>

      <div
        v-if="!activities.activities.length"
        class="mt-12 rounded-6 border border-outline-green-2 bg-surface-base p-10 text-center"
      >
        <p class="text-p-sm text-ink-gray-5">{{ activities.error || t('activity.empty') }}</p>
      </div>

      <div v-else class="mt-12 grid gap-4 md:grid-cols-3">
        <router-link
          v-for="item in activities.activities.slice(0, 3)"
          :key="item.id"
          :to="{ name: 'ActivityPost', params: { slug: item.slug } }"
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
            class="flex aspect-[16/9] w-full items-center justify-center bg-surface-green-2 text-ink-green-7"
          >
            <span class="lucide-camera size-8" aria-hidden="true" />
          </div>
          <div class="flex flex-1 flex-col p-5">
            <p v-if="item.publishedOn" class="text-2xs-medium text-ink-gray-4">
              {{ formatDate(item.publishedOn) }}
            </p>
            <h3
              class="mt-2 text-base-semibold leading-snug text-ink-gray-8 group-hover:text-ink-gray-9"
            >
              {{ item.title }}
            </h3>
            <p class="mt-2 flex-1 text-p-sm text-ink-gray-6">{{ item.excerpt }}</p>
            <span
              class="mt-4 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
            >
              {{ t('activity.list.readMore') }}
              <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
            </span>
          </div>
        </router-link>
      </div>
    </div>
  </section>
</template>
