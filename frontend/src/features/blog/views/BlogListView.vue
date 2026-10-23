<script setup lang="ts">
import { Button, ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { brand } from '@/shared/brand'
import { formatDate } from '@/shared/format'

import { useBlogStore } from '../store'

const blog = useBlogStore()

const pageCount = computed(() => Math.max(1, Math.ceil(blog.total / blog.perPage)))
const hasPrev = computed(() => blog.page > 1)
const hasNext = computed(() => blog.page < pageCount.value)

onMounted(async () => {
  await blog.fetchList()
  window.scrollTo({ top: 0 })
})

async function goTo(nextPage: number) {
  await blog.fetchList(nextPage)
  window.scrollTo({ top: 0 })
}
</script>

<template>
  <div id="top" class="min-h-screen bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main class="mx-auto w-full max-w-6xl px-5 py-12">
      <header class="mb-10 max-w-2xl">
        <h1 class="text-4xl-bold text-ink-gray-9">Blog</h1>
        <p class="mt-3 text-p-sm text-ink-gray-6">
          News, updates, and deep dives from the {{ brand.name }} team.
        </p>
      </header>

      <ErrorMessage v-if="blog.error" :message="blog.error" />

      <div v-else-if="blog.loading && !blog.posts.length" class="space-y-4">
        <div v-for="i in 3" :key="i" class="h-40 animate-pulse rounded-6 bg-surface-elevation-2" />
      </div>

      <div v-else-if="!blog.posts.length" class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center">
        <p class="text-p-sm text-ink-gray-5">No posts yet.</p>
      </div>

      <div v-else class="space-y-4">
        <router-link
          v-for="post in blog.posts"
          :key="post.id"
          :to="{ name: 'BlogPost', params: { slug: post.slug } }"
          class="group block rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors hover:border-outline-gray-2"
        >
          <img
            v-if="post.coverImage"
            :src="post.coverImage"
            alt=""
            class="mb-4 aspect-[21/9] w-full rounded-4 object-cover"
          />
          <div class="flex flex-wrap items-center gap-2 text-2xs-medium text-ink-gray-4">
            <span v-if="post.publishedOn">{{ formatDate(post.publishedOn) }}</span>
            <span v-if="post.authorName">· {{ post.authorName }}</span>
          </div>
          <h2 class="mt-2 text-xl-semibold text-ink-gray-8 transition-colors group-hover:text-ink-gray-9">
            {{ post.title }}
          </h2>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ post.excerpt }}</p>
          <span class="mt-3 inline-flex items-center gap-1 text-p-sm-medium text-ink-gray-7 transition-colors group-hover:text-ink-gray-9">
            Read more
            <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
          </span>
        </router-link>

        <div v-if="pageCount > 1" class="flex items-center justify-between pt-4">
          <Button
            label="Previous"
            size="sm"
            variant="subtle"
            icon-left="lucide-arrow-left"
            :disabled="!hasPrev || blog.loading"
            @click="goTo(blog.page - 1)"
          />
          <span class="text-p-sm text-ink-gray-4">
            Page {{ blog.page }} of {{ pageCount }}
          </span>
          <Button
            label="Next"
            size="sm"
            variant="subtle"
            icon-right="lucide-arrow-right"
            :disabled="!hasNext || blog.loading"
            @click="goTo(blog.page + 1)"
          />
        </div>
      </div>
    </main>
    <LandingFooter />
  </div>
</template>
