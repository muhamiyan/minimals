<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Spinner } from 'frappe-ui'

import { useBlogStore } from '@/features/blog/store'

import AboutSection from '../components/AboutSection.vue'
import CtaSection from '../components/CtaSection.vue'
import FeaturesSection from '../components/FeaturesSection.vue'
import HeroSection from '../components/HeroSection.vue'
import LandingFooter from '../components/LandingFooter.vue'
import LandingNav from '../components/LandingNav.vue'

const blog = useBlogStore()

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
    <Spinner v-if="!gateReady" class="mx-auto flex py-24" />
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
