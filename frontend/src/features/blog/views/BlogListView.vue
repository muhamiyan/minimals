<script setup lang="ts">
import { Button, ErrorMessage } from 'frappe-ui'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { brand } from '@/shared/brand'

import PostMeta from '../components/PostMeta.vue'
import { useBlogStore } from '../store'

const { t } = useI18n()
const blog = useBlogStore()

const gateReady = computed(() => blog.checked)
const pageCount = computed(() => Math.max(1, Math.ceil(blog.total / blog.perPage)))
const hasPrev = computed(() => blog.page > 1)
const hasNext = computed(() => blog.page < pageCount.value)

onMounted(async () => {
  if (!blog.checked) await blog.fetchList()
  window.scrollTo({ top: 0 })
})

async function goTo(nextPage: number) {
  await blog.fetchList(nextPage)
  window.scrollTo({ top: 0 })
}
</script>

<template>
  <div id="top" class="landing-scope flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <main v-if="!gateReady" class="mx-auto w-full max-w-6xl flex-1 px-5 py-12">
      <div class="mb-10 max-w-2xl space-y-3">
        <div class="shimmer h-9 w-40 rounded-4" />
        <div class="shimmer h-4 w-72 rounded-4" />
      </div>
      <div class="space-y-4">
        <div v-for="i in 3" :key="i" class="shimmer h-40 rounded-6" />
      </div>
    </main>
    <main v-else class="mx-auto w-full max-w-6xl flex-1 px-5 py-12">
      <header class="mb-10 max-w-2xl">
        <h1 class="text-4xl-bold text-ink-gray-9">{{ t('blog.title') }}</h1>
        <p class="mt-3 text-p-sm text-ink-gray-6">
          {{ t('blog.list.subtitle', { name: brand.name }) }}
        </p>
      </header>

      <ErrorMessage v-if="blog.error" :message="blog.error" />

      <div v-else-if="blog.loading && !blog.posts.length" class="space-y-4">
        <div v-for="i in 3" :key="i" class="shimmer h-40 rounded-6" />
      </div>

      <div v-else-if="!blog.posts.length" class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center">
        <p class="text-p-sm text-ink-gray-5">{{ t('blog.empty') }}</p>
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
          <PostMeta
            :published-on="post.publishedOn"
            :author="post.author || post.authorName"
            :category="post.category"
            :read-time="post.readTime"
          />
          <h2 class="mt-2 text-xl-semibold text-ink-gray-8 transition-colors group-hover:text-ink-gray-9">
            {{ post.title }}
          </h2>
          <p class="mt-2 text-p-sm text-ink-gray-6">{{ post.excerpt }}</p>
          <span class="mt-3 inline-flex items-center gap-1 text-p-sm-medium text-ink-gray-7 transition-colors group-hover:text-ink-gray-9">
            {{ t('blog.list.readMore') }}
            <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
          </span>
        </router-link>

        <div v-if="pageCount > 1" class="flex items-center justify-between pt-4">
          <Button
            :label="t('shared.prevPage')"
            size="sm"
            variant="subtle"
            icon-left="lucide-arrow-left"
            :disabled="!hasPrev || blog.loading"
            @click="goTo(blog.page - 1)"
          />
          <span class="text-p-sm text-ink-gray-4">
            {{ t('shared.pageOf', { page: blog.page, total: pageCount }) }}
          </span>
          <Button
            :label="t('shared.nextPage')"
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
