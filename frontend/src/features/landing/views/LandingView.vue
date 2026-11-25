<script setup lang="ts">
import { onMounted } from 'vue'

import ContactSection from '../components/ContactSection.vue'
import CtaSection from '../components/CtaSection.vue'
import HeroSection from '../components/HeroSection.vue'
import LandingFooter from '../components/LandingFooter.vue'
import LandingNav from '../components/LandingNav.vue'
import LoopSection from '../components/LoopSection.vue'
import PartnershipSection from '../components/PartnershipSection.vue'
import PillarsSection from '../components/PillarsSection.vue'
import ResourcesSection from '../components/ResourcesSection.vue'
import { useLandingContent } from '../useLandingContent'

const { ensure } = useLandingContent()

onMounted(() => {
  void ensure()
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
  <div id="top" class="landing-scope flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main class="flex-1">
      <HeroSection />
      <LoopSection />
      <PillarsSection />
      <ResourcesSection />
      <PartnershipSection />
      <ContactSection />
      <CtaSection />
    </main>
    <LandingFooter />
  </div>
</template>
