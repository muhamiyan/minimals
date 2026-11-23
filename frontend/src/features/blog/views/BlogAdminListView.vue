<script setup lang="ts">
import Shimmer from '@/shared/components/Shimmer.vue'
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Badge, Button, ErrorMessage } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDate } from '@/shared/format'

import { useBlogStore } from '../store'

const { t } = useI18n()
const blog = useBlogStore()

const gateReady = computed(() => blog.checked)
const pageCount = computed(() => Math.max(1, Math.ceil(blog.total / blog.perPage)))
const hasPrev = computed(() => blog.page > 1)
const hasNext = computed(() => blog.page < pageCount.value)

onMounted(async () => {
  if (!blog.checked) await blog.fetchAdminList()
})

async function goTo(nextPage: number) {
  await blog.fetchAdminList(nextPage)
  window.scrollTo({ top: 0 })
}
</script>

<template>
  <ShimmerPage v-if="!gateReady" />
  <div v-else class="mx-auto w-full max-w-5xl p-6">
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl-semibold text-ink-gray-9">{{ t('blog.title') }}</h1>
        <p class="mt-1 text-p-sm text-ink-gray-5">{{ t('blog.admin.subtitle') }}</p>
      </div>
      <Button
        :label="t('blog.admin.newPost')"
        variant="solid"
        theme="green"
        icon-left="lucide-plus"
        :route="{ name: 'BlogAdminCreate' }"
      />
    </header>

    <ErrorMessage v-if="blog.error" :message="blog.error" />

    <div v-else-if="blog.loading && !blog.posts.length" class="space-y-3">
      <Shimmer v-for="i in 4" :key="i" class="h-14  rounded-6 bg-surface-elevation-2" />
    </div>

    <div
      v-else-if="!blog.posts.length"
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center"
    >
      <p class="text-p-sm text-ink-gray-5">{{ t('blog.empty') }}</p>
      <Button
        class="mt-4"
        :label="t('blog.admin.createFirst')"
        variant="subtle"
        icon-left="lucide-plus"
        :route="{ name: 'BlogAdminCreate' }"
      />
    </div>

    <List v-else :columns="['minmax(0,1fr)', '7rem', '7rem']">
      <ListHeader>
        <ListHeaderCell>{{ t('blog.admin.columns.title') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('blog.admin.columns.status') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('blog.admin.columns.created') }}</ListHeaderCell>
      </ListHeader>
      <ListRows :items="blog.posts" v-slot="{ item }">
        <ListRow :route="{ name: 'BlogAdminEdit', params: { slug: item.slug } }">
          <ListCell>
            <span class="text-base-medium text-ink-gray-9">{{ item.title }}</span>
            <p class="truncate text-p-sm text-ink-gray-5">{{ item.excerpt }}</p>
          </ListCell>
          <ListCell>
            <Badge
              :label="item.status"
              :theme="item.status === 'published' ? 'green' : 'gray'"
              variant="subtle"
            />
          </ListCell>
          <ListCell>
            <span class="text-p-sm text-ink-gray-5">{{ formatDate(item.createdOn) }}</span>
          </ListCell>
        </ListRow>
      </ListRows>
    </List>

    <div v-if="pageCount > 1" class="mt-4 flex items-center justify-between">
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
</template>
