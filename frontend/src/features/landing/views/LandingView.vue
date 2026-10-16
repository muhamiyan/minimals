<script setup lang="ts">
import { onMounted } from 'vue'

import AboutSection from '../components/AboutSection.vue'
import CtaSection from '../components/CtaSection.vue'
import FeaturesSection from '../components/FeaturesSection.vue'
import HeroSection from '../components/HeroSection.vue'
import LandingFooter from '../components/LandingFooter.vue'
import LandingNav from '../components/LandingNav.vue'

onMounted(() => {
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
    <main>
      <HeroSection />
      <FeaturesSection />
      <AboutSection />
      <CtaSection />
    </main>
    <LandingFooter />
  </div>
</template>
