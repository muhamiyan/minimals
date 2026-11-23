<script setup lang="ts">
import Shimmer from './Shimmer.vue'
</script>

<template>
  <div class="mx-auto w-full max-w-6xl px-5 py-12" aria-busy="true" aria-label="Loading">
    <Shimmer class="h-9 w-64 max-w-full rounded-4" />
    <Shimmer class="mt-4 h-4 w-96 max-w-full rounded-4" />
    <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Shimmer v-for="i in 3" :key="i" class="h-52 rounded-6" />
    </div>
  </div>
</template>
