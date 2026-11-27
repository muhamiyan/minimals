<script setup lang="ts">
import { ErrorMessage } from 'frappe-ui'
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import LandingFooter from '@/features/landing/components/LandingFooter.vue'
import LandingNav from '@/features/landing/components/LandingNav.vue'
import { brand } from '@/shared/brand'

import BlogPostSkeleton from '../components/BlogPostSkeleton.vue'
import PostMeta from '../components/PostMeta.vue'
import { useBlogStore } from '../store'

const route = useRoute()
const blog = useBlogStore()
const { t, locale } = useI18n()

const slug = computed(() => String(route.params.slug || ''))
const gateReady = computed(() => blog.checked)

function applyTitle() {
  if (blog.post) {
    document.title = `${blog.post.title} · ${brand.name}`
  }
}

async function load() {
  await blog.fetchPost(slug.value)
  applyTitle()
  window.scrollTo({ top: 0 })
}

onMounted(async () => {
  await load()
})
watch(slug, load)
watch(locale, applyTitle)
</script>

<template>
  <div id="top" class="flex min-h-screen flex-col bg-surface-base text-ink-gray-8">
    <LandingNav />
    <BlogPostSkeleton v-if="!gateReady" />
    <main v-else class="mx-auto w-full max-w-3xl px-5 py-12">
      <router-link
        :to="{ name: 'BlogList' }"
        class="mb-8 inline-flex items-center gap-1.5 text-p-sm-medium text-ink-gray-6 transition-colors hover:text-ink-gray-9"
      >
        <span class="lucide-arrow-left size-3.5" aria-hidden="true" />
        {{ t('blog.post.back') }}
      </router-link>

      <BlogPostSkeleton v-if="blog.loadingPost" />

      <ErrorMessage v-else-if="blog.error" :message="blog.error" />

      <article v-else-if="blog.post">
        <header class="border-l-4 border-outline-green-4 pl-4">
          <h1 class="text-4xl-bold text-ink-gray-9">{{ blog.post.title }}</h1>
          <PostMeta
            class="mt-3"
            :published-on="blog.post.publishedOn"
            :author="blog.post.author"
            :author-name="blog.post.authorName"
            :category="blog.post.category"
            :read-time="blog.post.readTime"
          />
        </header>

        <img
          v-if="blog.post.coverImage"
          :src="blog.post.coverImage"
          alt=""
          class="mt-8 aspect-[21/9] w-full rounded-6 object-cover"
        />

        <div class="post-body mt-8 text-p-sm leading-relaxed text-ink-gray-7" v-html="blog.post.body" />
      </article>
    </main>
    <LandingFooter class="mt-auto" />
  </div>
</template>

<style scoped>
.post-body :deep(h1),
.post-body :deep(h2) {
  margin-top: 1.75rem;
  font-size: 1.375rem;
  font-weight: 700;
}

.post-body :deep(h3) {
  margin-top: 1.5rem;
  font-size: 1.125rem;
  font-weight: 600;
}

.post-body :deep(p) {
  margin-top: 0.875rem;
}

.post-body :deep(ul),
.post-body :deep(ol) {
  margin-top: 0.875rem;
  padding-left: 1.5rem;
}

.post-body :deep(ul) {
  list-style: disc;
}

.post-body :deep(ol) {
  list-style: decimal;
}

.post-body :deep(li) {
  margin-top: 0.375rem;
}

.post-body :deep(a) {
  text-decoration: underline;
}

.post-body :deep(img) {
  margin-top: 1rem;
  max-width: 100%;
  border-radius: 0.75rem;
}

.post-body :deep(blockquote) {
  margin-top: 0.875rem;
  padding-left: 1rem;
  border-left: 3px solid var(--outline-gray-2);
}
</style>
