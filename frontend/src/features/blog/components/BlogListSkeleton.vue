<template>
  <div class="mx-auto w-full max-w-6xl px-5 py-12">
    <div class="mb-10 max-w-2xl">
      <div class="shimmer h-9 w-48 rounded-4" />
      <div class="shimmer mt-3 h-5 w-full max-w-md rounded-4" />
    </div>
    <div class="space-y-4">
      <div
        v-for="i in 3"
        :key="i"
        class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="flex flex-wrap gap-2">
          <div class="shimmer h-5 w-24 rounded-full" />
          <div class="shimmer h-5 w-20 rounded-full" />
          <div class="shimmer h-5 w-28 rounded-full" />
        </div>
        <div class="shimmer mt-4 h-6 w-2/3 rounded-4" />
        <div class="shimmer mt-3 h-4 w-full rounded-4" />
        <div class="shimmer mt-2 h-4 w-5/6 rounded-4" />
        <div class="shimmer mt-4 h-4 w-24 rounded-4" />
      </div>
    </div>
  </div>
</template>
