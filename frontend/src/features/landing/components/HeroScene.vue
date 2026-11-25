<script setup lang="ts">
import { useColorScheme } from 'frappe-ui'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { HeroScene } from '../scene/heroScene'

const host = ref<HTMLDivElement | null>(null)
const { resolvedColorScheme } = useColorScheme()

let scene: HeroScene | null = null
let observer: IntersectionObserver | null = null
let motion: MediaQueryList | null = null
let inView = true
let destroyed = false

function applyPause() {
  scene?.setPaused(document.hidden || !inView)
}

function onMotionChange() {
  scene?.setReducedMotion(motion?.matches ?? false)
}

function onVisibility() {
  applyPause()
}

async function boot() {
  if (!host.value) return
  const { createHeroScene } = await import('../scene/heroScene')
  if (destroyed || !host.value) return
  try {
    scene = createHeroScene(host.value)
  } catch {
    return
  }
  motion = window.matchMedia('(prefers-reduced-motion: reduce)')
  motion.addEventListener('change', onMotionChange)
  document.addEventListener('visibilitychange', onVisibility)
  observer = new IntersectionObserver((entries) => {
    inView = entries[0]?.isIntersecting ?? true
    applyPause()
  })
  observer.observe(host.value)
  onMotionChange()
  applyPause()
  scene.syncPalette()
}

watch(resolvedColorScheme, async () => {
  await nextTick()
  scene?.syncPalette()
})

onMounted(boot)

onBeforeUnmount(() => {
  destroyed = true
  observer?.disconnect()
  motion?.removeEventListener('change', onMotionChange)
  document.removeEventListener('visibilitychange', onVisibility)
  scene?.destroy()
  scene = null
})
</script>

<template>
  <div ref="host" class="absolute inset-0" aria-hidden="true" />
</template>
