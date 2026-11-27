<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'

import { useProgramStore } from '../store'

const { t } = useI18n()
const programs = useProgramStore()

const gateReady = computed(() => programs.checked)

onMounted(async () => {
  if (!programs.checked) await programs.fetchList()
  window.scrollTo({ top: 0 })
})
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-6xl px-5 py-12">
      <header class="mb-10 max-w-2xl rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('program.title') }}</h1>
        <p class="mt-3 text-p-sm text-ink-gray-6">{{ t('program.lead') }}</p>
      </header>

      <ErrorMessage v-if="programs.error" :message="programs.error" />

      <div
        v-else-if="!programs.programs.length"
        class="rounded-6 border border-outline-green-2 bg-surface-base p-10 text-center"
      >
        <p class="text-p-sm text-ink-gray-5">{{ t('program.empty') }}</p>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="item in programs.programs"
          :key="item.id"
          :to="{ name: 'ProgramPost', params: { slug: item.slug } }"
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
            <span class="lucide-graduation-cap size-8" aria-hidden="true" />
          </div>
          <div class="flex flex-1 flex-col p-5">
            <p class="text-2xs-medium uppercase tracking-wide text-ink-green-7">
              {{ item.level }}
            </p>
            <h2
              class="mt-2 text-lg-semibold leading-snug text-ink-gray-8 group-hover:text-ink-gray-9"
            >
              {{ item.title }}
            </h2>
            <p class="mt-2 flex-1 text-p-sm text-ink-gray-6">{{ item.excerpt }}</p>
            <span
              class="mt-4 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
            >
              {{ t('program.list.readMore') }}
              <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
            </span>
          </div>
        </router-link>
      </div>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>
