<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Spinner } from 'frappe-ui'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate } from '@/shared/format'

import { useActivityStore, type ActivitySummary } from '../store'

const { t } = useI18n()
const router = useRouter()
const activities = useActivityStore()

const gateReady = computed(() => activities.checked)
const empty = computed(() => !activities.loading && activities.activities.length === 0)

const columns = {
  base: ['minmax(0,1fr)', '6rem', '3rem'],
  md: ['minmax(0,2fr)', '6rem', '6.5rem', '3rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  initialPerPage: activities.perPage,
  setPage: (page) => {
    activities.page = page
  },
  fetch: (query) =>
    activities.fetchAdminList({
      search: query.search,
      page: activities.page,
      perPage: query.perPage,
    }),
})

function openActivity(activity: ActivitySummary) {
  void router.push({ name: 'ActivityAdminEdit', params: { slug: activity.slug } })
}

onMounted(async () => {
  await refresh()
})
</script>

<template>
  <AppPageHeader>
    <template #default>
      <Button
        variant="solid"
        theme="gray"
        icon-left="lucide-plus"
        :label="t('activity.admin.newActivity')"
        :route="{ name: 'ActivityAdminCreate' }"
      />
    </template>
    <template #suffix>
      <Button
        variant="ghost"
        theme="gray"
        icon="lucide-plus"
        :label="t('activity.admin.newActivity')"
        :route="{ name: 'ActivityAdminCreate' }"
      />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('activity.admin.searchPosts')"
    />

    <div>
      <ListState
        :loading="activities.loading"
        :error="activities.error"
        :empty="empty"
        icon="lucide-calendar-days"
        :empty-message="search ? t('activity.admin.noActivitiesFound') : t('activity.empty')"
      >
        <template #action>
          <Button
            variant="outline"
            theme="gray"
            icon-left="lucide-plus"
            :label="t('activity.admin.createFirst')"
            :route="{ name: 'ActivityAdminCreate' }"
          />
        </template>

        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('activity.admin.columns.title') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('activity.admin.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('activity.admin.columns.created') }}
            </ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('activity.admin.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="activities.activities" v-slot="{ item }">
            <ListRow :value="item.id" @click="openActivity(item)">
              <ListCell>
                <span class="block truncate text-base-medium text-ink-gray-8">
                  {{ item.title }}
                </span>
              </ListCell>
              <ListCell>
                <Badge
                  :label="
                    item.status === 'published'
                      ? t('activity.admin.form.published')
                      : t('activity.admin.form.draft')
                  "
                  :theme="item.status === 'published' ? 'green' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="truncate text-p-sm text-ink-gray-5">
                  {{ formatDate(item.createdOn) }}
                </span>
              </ListCell>
              <ListCell>
                <Button
                  variant="ghost"
                  theme="gray"
                  icon="lucide-pencil"
                  :label="t('activity.admin.editActivity')"
                  @click.stop="openActivity(item)"
                />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!activities.loading && !activities.error && !empty"
        :total="activities.total"
        :page="activities.page"
        :per-page="activities.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>
</template>
