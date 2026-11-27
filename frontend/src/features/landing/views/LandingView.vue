<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { computed, onMounted } from 'vue'


import { useActivityStore } from '@/features/activity/store'
import { useBlogStore } from '@/features/blog/store'
import { useProgramStore } from '@/features/program/store'
import { useScholarshipStore } from '@/features/scholarship/store'

import ScholarshipsSection from '@/features/scholarship/components/ScholarshipsSection.vue'

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

const blog = useBlogStore()
const activity = useActivityStore()
const program = useProgramStore()
const scholarship = useScholarshipStore()

const gateReady = computed(
  () => blog.checked && activity.checked && program.checked && scholarship.checked,
)

onMounted(async () => {
  await Promise.all([
    blog.checked ? Promise.resolve() : blog.fetchList(1),
    activity.checked ? Promise.resolve() : activity.fetchList(1),
    program.checked ? Promise.resolve() : program.fetchList(),
    scholarship.checked ? Promise.resolve() : scholarship.fetchList(),
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
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <ShimmerPage v-if="!gateReady" />
    <template v-else>
      <main>
        <HeroSection />
        <FeaturesSection />
        <AboutSection />
        <FacilitiesSection />
        <ProgramsSection />
        <ScholarshipsSection />
        <ActivitiesSection />
        <PostsSection />
        <CtaSection />
        <ContactSection />
      </main>
      <LandingFooter class="mt-auto" />
    </template>
  </div>
</template>
