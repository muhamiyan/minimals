<script setup lang="ts">
import { Button } from 'frappe-ui'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { heroSlides, PPDB_URL } from '../content'

const { t } = useI18n()

const infoCards = [
  { icon: 'lucide-calendar-days', label: 'landing.hero.periodLabel', value: 'landing.hero.period' },
  { icon: 'lucide-clock', label: 'landing.hero.hoursLabel', value: 'landing.hero.hours' },
  { icon: 'lucide-map-pin', label: 'landing.hero.locationLabel', value: 'landing.hero.location' },
]

const current = ref(0)
const paused = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

const hasSlides = computed(() => heroSlides.length > 0)

function goTo(index: number) {
  if (!heroSlides.length) return
  current.value = (index + heroSlides.length) % heroSlides.length
}

function restartTimer() {
  if (timer) clearInterval(timer)
  timer = null
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  timer = setInterval(() => {
    if (!paused.value) goTo(current.value + 1)
  }, 6000)
}

function select(index: number) {
  goTo(index)
  restartTimer()
}

onMounted(restartTimer)

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function scrollToAbout() {
  document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <section
    class="relative overflow-hidden border-b border-outline-green-2 bg-surface-green-9"
    @mouseenter="paused = true"
    @mouseleave="paused = false"
    @focusin="paused = true"
    @focusout="paused = false"
  >
    <div v-if="hasSlides" aria-hidden="true" class="absolute inset-0">
      <img
        v-for="(src, i) in heroSlides"
        :key="src"
        :src="src"
        alt=""
        class="absolute inset-0 size-full object-cover transition-opacity duration-700 motion-reduce:transition-none"
        :class="i === current ? 'opacity-100' : 'opacity-0'"
      />
    </div>
    <div class="absolute inset-0 bg-surface-green-9/70" aria-hidden="true" />

    <div class="relative mx-auto w-full max-w-6xl px-5 pb-14 pt-16 sm:pt-24">
      <h1 class="mx-auto max-w-4xl text-center text-6xl-bold text-ink-gray-1 sm:text-9xl-bold">
        {{ t('landing.hero.title') }}
        <span class="text-ink-green-3">{{ t('landing.hero.accent') }}</span>.
      </h1>

      <p class="mx-auto mt-5 max-w-2xl text-center text-p-lg text-ink-gray-3">
        {{ t('landing.hero.lead') }}
      </p>

      <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button
          :label="t('landing.hero.ctaPpdb')"
          :href="PPDB_URL"
          size="lg"
          variant="solid"
          theme="green"
          icon-right="lucide-arrow-up-right"
        />
        <Button
          :label="t('landing.hero.ctaProfile')"
          size="lg"
          variant="outline"
          theme="gray"
          icon-left="lucide-info"
          @click="scrollToAbout"
        />
      </div>

      <div class="mx-auto mt-14 grid w-full max-w-3xl gap-3 sm:grid-cols-3">
        <div
          v-for="item in infoCards"
          :key="item.label"
          class="rounded-6 border border-outline-green-5 bg-surface-green-9/70 p-4 text-left"
        >
          <div class="w-fit rounded-4 bg-surface-green-7 p-2 text-ink-gray-1">
            <span :class="item.icon" class="size-5" aria-hidden="true" />
          </div>
          <p class="mt-3 text-2xs-medium uppercase tracking-wide text-ink-gray-4">
            {{ t(item.label) }}
          </p>
          <p class="mt-1 text-base-semibold text-ink-gray-1">{{ t(item.value) }}</p>
        </div>
      </div>

    </div>

    <div
      v-if="hasSlides"
      class="absolute bottom-5 left-1/2 flex -translate-x-1/2 items-center gap-2"
    >
      <button
        v-for="(src, i) in heroSlides"
        :key="src"
        type="button"
        class="size-2 rounded-full transition-colors motion-reduce:transition-none"
        :class="i === current ? 'bg-surface-green-7' : 'bg-ink-gray-1/50 hover:bg-ink-gray-1/80'"
        :aria-label="t('landing.hero.slide', { n: i + 1 })"
        :aria-current="i === current ? 'true' : undefined"
        @click="select(i)"
      />
    </div>
  </section>
</template>
