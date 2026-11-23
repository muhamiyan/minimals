<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { useProgramStore } from '@/features/program/store'

const { t } = useI18n()
const programs = useProgramStore()

const gateReady = computed(() => programs.checked)

onMounted(async () => {
  if (!programs.checked) await programs.fetchList()
})
</script>

<template>
  <div id="top" class="min-h-screen bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-4xl px-5 py-12">
      <header class="mb-10 rounded-6 border border-outline-green-2 bg-surface-green-1 px-6 py-6">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('structure.title') }}</h1>
        <p class="mt-3 text-p-base text-ink-gray-6">{{ t('structure.lead') }}</p>
      </header>

      <ErrorMessage v-if="programs.error" :message="programs.error" />

      <div v-else-if="!programs.programs.length" class="rounded-6 border border-outline-green-2 bg-surface-base p-10 text-center">
        <p class="text-p-sm text-ink-gray-5">{{ t('program.empty') }}</p>
      </div>

      <div v-else class="space-y-3">
        <router-link
          v-for="item in programs.programs"
          :key="item.id"
          :to="{ name: 'ProgramPost', params: { slug: item.slug } }"
          class="flex items-center gap-4 rounded-6 border border-outline-green-2 bg-surface-base p-4 transition-colors hover:border-outline-green-3"
        >
          <img
            v-if="item.coverImage"
            :src="item.coverImage"
            alt=""
            class="size-14 shrink-0 rounded-4 object-cover"
          />
          <span
            v-else
            class="flex size-14 shrink-0 items-center justify-center rounded-4 bg-surface-green-1 text-ink-green-7"
          >
            <span class="lucide-school size-5" aria-hidden="true" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block text-2xs-medium uppercase tracking-wide text-ink-gray-5">
              {{ item.level }}
            </span>
            <span class="mt-1 block text-base-medium text-ink-gray-9">{{ item.title }}</span>
          </span>
          <span class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4" aria-hidden="true" />
        </router-link>
      </div>
    </main>
    <LandingFooter />
  </div>
</template>
