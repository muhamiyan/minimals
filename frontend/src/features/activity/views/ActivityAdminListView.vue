<script setup lang="ts">
import Shimmer from '@/shared/components/Shimmer.vue'
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Badge, Button, ErrorMessage } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDate } from '@/shared/format'

import { useActivityStore } from '../store'

const { t } = useI18n()
const activities = useActivityStore()

const gateReady = computed(() => activities.checked)
const pageCount = computed(() =>
  Math.max(1, Math.ceil(activities.total / activities.perPage)),
)
const hasPrev = computed(() => activities.page > 1)
const hasNext = computed(() => activities.page < pageCount.value)

onMounted(async () => {
  if (!activities.checked) await activities.fetchAdminList()
})

async function goTo(nextPage: number) {
  await activities.fetchAdminList(nextPage)
  window.scrollTo({ top: 0 })
}
</script>

<template>
  <ShimmerPage v-if="!gateReady" />
  <div v-else class="mx-auto w-full max-w-5xl p-6">
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl-semibold text-ink-gray-9">{{ t('activity.title') }}</h1>
        <p class="mt-1 text-p-sm text-ink-gray-5">{{ t('activity.admin.subtitle') }}</p>
      </div>
      <Button
        :label="t('activity.admin.newActivity')"
        variant="solid"
        theme="green"
        icon-left="lucide-plus"
        :route="{ name: 'ActivityAdminCreate' }"
      />
    </header>

    <ErrorMessage v-if="activities.error" :message="activities.error" />

    <div v-else-if="activities.loading && !activities.activities.length" class="space-y-3">
      <Shimmer v-for="i in 4" :key="i" class="h-14  rounded-6 bg-surface-elevation-2" />
    </div>

    <div
      v-else-if="!activities.activities.length"
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center"
    >
      <p class="text-p-sm text-ink-gray-5">{{ t('activity.empty') }}</p>
      <Button
        class="mt-4"
        :label="t('activity.admin.createFirst')"
        variant="subtle"
        icon-left="lucide-plus"
        :route="{ name: 'ActivityAdminCreate' }"
      />
    </div>

    <List v-else :columns="['minmax(0,1fr)', '7rem', '7rem']">
      <ListHeader>
        <ListHeaderCell>{{ t('activity.admin.columns.title') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('activity.admin.columns.status') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('activity.admin.columns.created') }}</ListHeaderCell>
      </ListHeader>
      <ListRows :items="activities.activities" v-slot="{ item }">
        <ListRow :route="{ name: 'ActivityAdminEdit', params: { slug: item.slug } }">
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
        :disabled="!hasPrev || activities.loading"
        @click="goTo(activities.page - 1)"
      />
      <span class="text-p-sm text-ink-gray-4">
        {{ t('shared.pageOf', { page: activities.page, total: pageCount }) }}
      </span>
      <Button
        :label="t('shared.nextPage')"
        size="sm"
        variant="subtle"
        icon-right="lucide-arrow-right"
        :disabled="!hasNext || activities.loading"
        @click="goTo(activities.page + 1)"
      />
    </div>
  </div>
</template>
