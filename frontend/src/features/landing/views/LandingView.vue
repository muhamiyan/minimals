<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { computed, onMounted } from 'vue'


import { useActivityStore } from '@/features/activity/store'
import { useBlogStore } from '@/features/blog/store'
import { useProgramStore } from '@/features/program/store'

import AboutSection from '../components/AboutSection.vue'
import ActivitiesSection from '../components/ActivitiesSection.vue'
import ContactSection from '../components/ContactSection.vue'
import CtaSection from '../components/CtaSection.vue'
import FacilitiesSection from '../components/FacilitiesSection.vue'
import FeaturesSection from '../components/FeaturesSection.vue'
import HeroSection from '../components/HeroSection.vue'
import LandingFooter from '../components/LandingFooter.vue'
import LandingNav from '../components/LandingNav.vue'
import PostsSection from '../components/PostsSection.vue'
import ProgramsSection from '../components/ProgramsSection.vue'
import SupportSection from '../components/SupportSection.vue'

const blog = useBlogStore()
const activity = useActivityStore()
const program = useProgramStore()

const gateReady = computed(() => blog.checked && activity.checked && program.checked)

onMounted(async () => {
  await Promise.all([
    blog.checked ? Promise.resolve() : blog.fetchList(1),
    activity.checked ? Promise.resolve() : activity.fetchList(1),
    program.checked ? Promise.resolve() : program.fetchList(),
  ])
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
    <ShimmerPage v-if="!gateReady" />
    <template v-else>
      <main>
        <HeroSection />
        <FeaturesSection />
        <AboutSection />
        <FacilitiesSection />
        <ProgramsSection />
        <ActivitiesSection />
        <PostsSection />
        <CtaSection />
        <SupportSection />
        <ContactSection />
      </main>
      <LandingFooter />
    </template>
  </div>
</template>
