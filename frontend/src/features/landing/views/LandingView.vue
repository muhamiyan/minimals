<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { useBlogStore } from '@/features/blog/store'

import AboutSection from '../components/AboutSection.vue'
import CtaSection from '../components/CtaSection.vue'
import FeaturesSection from '../components/FeaturesSection.vue'
import HeroSection from '../components/HeroSection.vue'
import LandingFooter from '../components/LandingFooter.vue'
import LandingNav from '../components/LandingNav.vue'

const blog = useBlogStore()
const { t } = useI18n()

const gateReady = computed(() => blog.checked)

onMounted(async () => {
  if (!blog.checked) await blog.fetchList(1)
  const id = window.location.hash.slice(1)
  const target = id ? document.getElementById(id) : null
  if (target) {
    target.scrollIntoView()
  } else {
    window.scrollTo({ top: 0 })
  }
})
</script>

<template>
  <div id="top" class="min-h-screen bg-surface-base text-ink-gray-8">
    <LandingNav />
    <div
      v-if="!gateReady"
      class="mx-auto w-full max-w-6xl px-5 py-12"
      role="status"
      aria-busy="true"
      :aria-label="t('blog.loading')"
    >
      <div class="shimmer mx-auto h-6 w-40 rounded-4" />
      <div class="shimmer mx-auto mt-5 h-14 w-3/4 rounded-6" />
      <div class="shimmer mx-auto mt-4 h-5 w-2/3 rounded-4" />
      <div class="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="i in 8" :key="i" class="shimmer h-24 rounded-6" />
      </div>
      <div class="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="shimmer h-56 rounded-6" />
        <div class="shimmer h-56 rounded-6" />
      </div>
    </div>
    <template v-else>
      <main>
        <HeroSection />
        <FeaturesSection />
        <AboutSection />
        <CtaSection />
      </main>
      <LandingFooter />
    </template>
  </div>
</template>
