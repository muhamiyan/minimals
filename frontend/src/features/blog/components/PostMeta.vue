<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDate } from '@/shared/format'

const props = withDefaults(
  defineProps<{
    publishedOn?: string | null
    author?: string | null
    authorName?: string | null
    category?: string | null
    readTime?: number | null
    large?: boolean
  }>(),
  { large: false },
)

const { t } = useI18n()

const authorLabel = computed(() => props.author || props.authorName || '')
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-x-3 gap-y-1.5 font-medium text-ink-gray-5"
    :class="large ? 'text-p-sm' : 'text-2xs'"
  >
    <span v-if="publishedOn" class="inline-flex items-center gap-1.5">
      <span class="lucide-calendar size-3.5 text-surface-blue-5" aria-hidden="true" />
      {{ formatDate(publishedOn) }}
    </span>
    <span v-if="authorLabel" class="inline-flex items-center gap-1.5">
      <span class="lucide-user size-3.5 text-surface-blue-5" aria-hidden="true" />
      {{ authorLabel }}
    </span>
    <span
      v-if="category"
      class="inline-flex items-center rounded-full bg-surface-blue-1 px-2 py-0.5 text-surface-blue-6"
    >
      {{ category }}
    </span>
    <span v-if="readTime" class="inline-flex items-center gap-1.5">
      <span class="lucide-clock size-3.5 text-surface-blue-5" aria-hidden="true" />
      {{ t('blog.list.readTime', { n: readTime }) }}
    </span>
  </div>
</template>