<script setup lang="ts">
import { logoBackdropClass, useBrandLogo } from '@/shared/brand'

withDefaults(
  defineProps<{
    size?: 'md' | 'lg' | 'fill'
    alt?: string
  }>(),
  { size: 'md', alt: '' },
)

const sizeClass = {
  md: 'size-12 rounded-6',
  lg: 'size-14 rounded-6',
  fill: 'h-full w-full',
} as const

const { logoSrc, logoTone, onLogoError } = useBrandLogo()
</script>

<template>
  <div
    class="overflow-hidden"
    :class="[sizeClass[size], logoBackdropClass(logoTone)]"
  >
    <img
      v-if="logoSrc"
      :src="logoSrc"
      :alt="alt"
        class="h-full w-full object-contain"
      @error="onLogoError"
    />
    <slot v-else />
  </div>
</template>
