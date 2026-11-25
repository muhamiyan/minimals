<template>
  <div class="mx-auto w-full max-w-3xl px-5 py-12">
    <div class="shimmer h-5 w-24 rounded-4" />
    <div class="shimmer mt-8 h-9 w-3/4 rounded-4" />
    <div class="mt-4 flex flex-wrap gap-2">
      <div class="shimmer h-5 w-24 rounded-full" />
      <div class="shimmer h-5 w-20 rounded-full" />
      <div class="shimmer h-5 w-28 rounded-full" />
    </div>
    <div class="shimmer mt-8 aspect-[21/9] w-full rounded-6" />
    <div class="mt-8 space-y-3">
      <div
        v-for="i in 6"
        :key="i"
        class="shimmer h-4 rounded-4"
        :class="i === 6 ? 'w-2/3' : 'w-full'"
      />
    </div>
  </div>
</template>