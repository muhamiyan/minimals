<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDate } from '@/shared/format'

interface Props {
  publishedOn?: string
  author?: string
  authorName?: string
  category?: string
  readTime?: number
}

const props = defineProps<Props>()
const { t } = useI18n()

const authorLabel = computed(() => props.author || props.authorName || '')
</script>

<template>
  <div class="flex flex-wrap items-center gap-2 text-2xs-medium">
    <span
      v-if="publishedOn"
      class="inline-flex items-center gap-1 rounded-full bg-surface-gray-2 px-2 py-0.5 text-ink-gray-6"
    >
      <span class="lucide-calendar size-3" aria-hidden="true" />
      {{ formatDate(publishedOn) }}
    </span>
    <span
      v-if="authorLabel"
      class="inline-flex items-center gap-1 rounded-full bg-surface-blue-2 px-2 py-0.5 text-ink-blue-6"
    >
      <span class="lucide-user size-3" aria-hidden="true" />
      {{ authorLabel }}
    </span>
    <span
      v-if="category"
      class="inline-flex items-center gap-1 rounded-full bg-surface-violet-2 px-2 py-0.5 text-ink-violet-6"
    >
      <span class="lucide-tag size-3" aria-hidden="true" />
      {{ category }}
    </span>
    <span
      v-if="readTime"
      class="inline-flex items-center gap-1 rounded-full bg-surface-amber-2 px-2 py-0.5 text-ink-amber-6"
    >
      <span class="lucide-clock size-3" aria-hidden="true" />
      {{ t('blog.list.readTime', { n: readTime }) }}
    </span>
  </div>
</template>