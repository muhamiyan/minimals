<script setup lang="ts">
import { Badge } from 'frappe-ui'
import { useI18n } from 'vue-i18n'

import { useBlogStore } from '@/features/blog/store'
import { formatDate } from '@/shared/format'

const { t } = useI18n()
const blog = useBlogStore()
</script>

<template>
  <section
    v-if="blog.posts.length"
    id="posts"
    class="border-t border-outline-gray-1 bg-surface-base"
  >
    <div class="mx-auto w-full max-w-6xl px-5 py-20">
      <div class="flex flex-wrap items-end justify-between gap-4">
        <div class="max-w-2xl">
          <Badge theme="green" variant="subtle" :label="t('landing.posts.badge')" />
          <h2 class="mt-4 text-5xl-bold text-ink-gray-9">{{ t('landing.posts.title') }}</h2>
          <p class="mt-3 text-p-base text-ink-gray-6">{{ t('landing.posts.lead') }}</p>
        </div>
        <router-link
          :to="{ name: 'BlogList' }"
          class="inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7"
        >
          {{ t('landing.posts.all') }}
          <span class="lucide-arrow-right size-3.5" aria-hidden="true" />
        </router-link>
      </div>

      <div class="mt-12 grid gap-4 md:grid-cols-3">
        <router-link
          v-for="post in blog.posts.slice(0, 3)"
          :key="post.id"
          :to="{ name: 'BlogPost', params: { slug: post.slug } }"
          class="group flex flex-col overflow-hidden rounded-6 border border-t-2 border-outline-gray-1 border-t-outline-green-4 bg-surface-green-1 transition-colors hover:border-outline-green-3 hover:bg-surface-green-2"
        >
          <img
            v-if="post.coverImage"
            :src="post.coverImage"
            alt=""
            class="aspect-[16/9] w-full object-cover"
          />
          <div
            v-else
            class="flex aspect-[16/9] w-full items-center justify-center bg-surface-green-2 text-ink-green-7"
          >
            <span class="lucide-newspaper size-8" aria-hidden="true" />
          </div>
          <div class="flex flex-1 flex-col p-5">
            <p v-if="post.publishedOn" class="text-2xs-medium text-ink-gray-4">
              {{ formatDate(post.publishedOn) }}
            </p>
            <h3 class="mt-2 text-base-semibold leading-snug text-ink-gray-8 group-hover:text-ink-gray-9">
              {{ post.title }}
            </h3>
            <p class="mt-2 flex-1 text-p-sm text-ink-gray-6">{{ post.excerpt }}</p>
            <span class="mt-4 inline-flex items-center gap-1 text-p-sm-medium text-ink-green-7">
              {{ t('blog.list.readMore') }}
              <span class="lucide-chevron-right size-3.5" aria-hidden="true" />
            </span>
          </div>
        </router-link>
      </div>
    </div>
  </section>
</template>
