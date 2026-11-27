<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'

import { useActivityStore } from '../store'

const { t } = useI18n()
const activities = useActivityStore()

const gateReady = computed(() => activities.checked)
const withCover = computed(() => activities.activities.filter((item) => item.coverImage))

onMounted(async () => {
  if (!activities.checked) await activities.fetchList()
  window.scrollTo({ top: 0 })
})
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-6xl px-5 py-12">
      <header class="mb-10 max-w-2xl rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('gallery.title') }}</h1>
        <p class="mt-3 text-p-sm text-ink-gray-6">{{ t('gallery.lead') }}</p>
      </header>

      <ErrorMessage v-if="activities.error" :message="activities.error" />

      <div
        v-else-if="!withCover.length"
        class="rounded-6 border border-outline-green-2 bg-surface-base p-10 text-center"
      >
        <p class="text-p-sm text-ink-gray-5">{{ t('gallery.empty') }}</p>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="item in withCover"
          :key="item.id"
          :to="{ name: 'ActivityPost', params: { slug: item.slug } }"
          class="group overflow-hidden rounded-6 border border-outline-green-2 bg-surface-base transition-colors hover:border-outline-green-3"
        >
          <img
            :src="item.coverImage"
            alt=""
            class="aspect-[4/3] w-full object-cover"
          />
          <div class="p-4">
            <h2
              class="text-base-semibold leading-snug text-ink-gray-8 group-hover:text-ink-gray-9"
            >
              {{ item.title }}
            </h2>
          </div>
        </router-link>
      </div>

      <div class="mt-10 text-center">
        <router-link
          :to="{ name: 'ActivityList' }"
          class="inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
        >
          {{ t('gallery.allActivities') }}
          <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
        </router-link>
      </div>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>
