<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Button, ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { brand } from '@/shared/brand'
import { formatDate } from '@/shared/format'

import { useActivityStore } from '../store'

const { t } = useI18n()
const activities = useActivityStore()

const gateReady = computed(() => activities.checked)
const pageCount = computed(() =>
  Math.max(1, Math.ceil(activities.total / activities.perPage)),
)
const hasPrev = computed(() => activities.page > 1)
const hasNext = computed(() => activities.page < pageCount.value)

onMounted(async () => {
  if (!activities.checked) await activities.fetchList()
  window.scrollTo({ top: 0 })
})

async function goTo(nextPage: number) {
  await activities.fetchList(nextPage)
  window.scrollTo({ top: 0 })
}
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-6xl px-5 py-12">
      <header class="mb-10 max-w-2xl rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('activity.title') }}</h1>
        <p class="mt-3 text-p-sm text-ink-gray-6">
          {{ t('activity.list.subtitle', { name: brand.name }) }}
        </p>
      </header>

      <ErrorMessage v-if="activities.error" :message="activities.error" />

      <div
        v-else-if="!activities.activities.length"
        class="rounded-6 border border-outline-green-2 bg-surface-base p-10 text-center"
      >
        <p class="text-p-sm text-ink-gray-5">{{ t('activity.empty') }}</p>
      </div>

      <div v-else class="space-y-4">
        <router-link
          v-for="item in activities.activities"
          :key="item.id"
          :to="{ name: 'ActivityPost', params: { slug: item.slug } }"
          class="group block overflow-hidden rounded-6 border border-outline-green-2 bg-surface-base transition-colors hover:border-outline-green-3"
        >
          <img
            v-if="item.coverImage"
            :src="item.coverImage"
            alt=""
            class="aspect-[21/9] w-full object-cover"
          />
          <div class="p-5">
            <p v-if="item.publishedOn" class="text-2xs-medium text-ink-gray-4">
              {{ formatDate(item.publishedOn) }}
            </p>
            <h2
              class="mt-2 text-xl-semibold text-ink-gray-8 transition-colors group-hover:text-ink-gray-9"
            >
              {{ item.title }}
            </h2>
            <p class="mt-2 text-p-sm text-ink-gray-6">{{ item.excerpt }}</p>
            <span
              class="mt-3 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
            >
              {{ t('activity.list.readMore') }}
              <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
            </span>
          </div>
        </router-link>

        <div v-if="pageCount > 1" class="flex items-center justify-between pt-4">
          <Button
            :label="t('shared.prevPage')"
            size="sm"
            variant="subtle"
            icon-left="lucide-arrow-left"
            :disabled="!hasPrev || activities.loading"
            @click="goTo(activities.page - 1)"
          />
          <span class="text-p-sm text-ink-gray-4">
            {{ t('shared.pageOf', { page: activities.page, total: pageCount }) }}
          </span>
          <Button
            :label="t('shared.nextPage')"
            size="sm"
            variant="subtle"
            icon-right="lucide-arrow-right"
            :disabled="!hasNext || activities.loading"
            @click="goTo(activities.page + 1)"
          />
        </div>
      </div>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>
