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

import { useScholarshipStore, type ScholarshipSummary } from '../store'

const { t } = useI18n()
const router = useRouter()
const scholarships = useScholarshipStore()

const gateReady = computed(() => scholarships.checked)
const empty = computed(() => !scholarships.loading && scholarships.scholarships.length === 0)

const columns = {
  base: ['minmax(0,1fr)', '5rem', '5rem', '4rem', '3rem'],
  md: ['minmax(0,2fr)', '6rem', '6rem', '4rem', '3rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  initialPerPage: scholarships.perPage,
  setPage: (page) => {
    scholarships.page = page
  },
  fetch: (query) =>
    scholarships.fetchAdminList({
      search: query.search,
      page: scholarships.page,
      perPage: query.perPage,
    }),
})

function openScholarship(scholarship: ScholarshipSummary) {
  void router.push({ name: 'ScholarshipAdminEdit', params: { slug: scholarship.slug } })
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
        :label="t('scholarship.admin.newScholarship')"
        :route="{ name: 'ScholarshipAdminCreate' }"
      />
    </template>
    <template #suffix>
      <Button
        variant="ghost"
        theme="gray"
        icon="lucide-plus"
        :label="t('scholarship.admin.newScholarship')"
        :route="{ name: 'ScholarshipAdminCreate' }"
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
      :placeholder="t('scholarship.admin.searchScholarships')"
    />

    <div>
      <ListState
        :loading="scholarships.loading"
        :error="scholarships.error"
        :empty="empty"
        icon="lucide-graduation-cap"
        :empty-message="search ? t('scholarship.admin.noScholarshipsFound') : t('scholarship.empty')"
      >
        <template #action>
          <Button
            variant="outline"
            theme="gray"
            icon-left="lucide-plus"
            :label="t('scholarship.admin.createFirst')"
            :route="{ name: 'ScholarshipAdminCreate' }"
          />
        </template>

        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('scholarship.admin.columns.title') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('scholarship.admin.columns.level') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('scholarship.admin.columns.status') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('scholarship.admin.columns.order') }}</ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('scholarship.admin.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="scholarships.scholarships" v-slot="{ item }">
            <ListRow :value="item.id" @click="openScholarship(item)">
              <ListCell>
                <span class="block truncate text-base-medium text-ink-gray-8">
                  {{ item.title }}
                </span>
              </ListCell>
              <ListCell>
                <span class="truncate text-p-sm text-ink-gray-5">{{ item.level }}</span>
              </ListCell>
              <ListCell>
                <Badge
                  :label="
                    item.status === 'published'
                      ? t('scholarship.admin.form.published')
                      : t('scholarship.admin.form.draft')
                  "
                  :theme="item.status === 'published' ? 'green' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell>
                <span class="truncate text-p-sm text-ink-gray-5">{{ item.order }}</span>
              </ListCell>
              <ListCell>
                <Button
                  variant="ghost"
                  theme="gray"
                  icon="lucide-pencil"
                  :label="t('scholarship.admin.editScholarship')"
                  @click.stop="openScholarship(item)"
                />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!scholarships.loading && !scholarships.error && !empty"
        :total="scholarships.total"
        :page="scholarships.page"
        :per-page="scholarships.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>
</template>
