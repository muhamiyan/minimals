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

import { useProgramStore, type ProgramSummary } from '../store'

const { t } = useI18n()
const router = useRouter()
const programs = useProgramStore()

const gateReady = computed(() => programs.checked)
const empty = computed(() => !programs.loading && programs.programs.length === 0)

const columns = {
  base: ['minmax(0,1fr)', '5rem', '5rem', '4rem', '3rem'],
  md: ['minmax(0,2fr)', '6rem', '6rem', '4rem', '3rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  initialPerPage: programs.perPage,
  setPage: (page) => {
    programs.page = page
  },
  fetch: (query) =>
    programs.fetchAdminList({
      search: query.search,
      page: programs.page,
      perPage: query.perPage,
    }),
})

function openProgram(program: ProgramSummary) {
  void router.push({ name: 'ProgramAdminEdit', params: { slug: program.slug } })
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
        :label="t('program.admin.newProgram')"
        :route="{ name: 'ProgramAdminCreate' }"
      />
    </template>
    <template #suffix>
      <Button
        variant="ghost"
        theme="gray"
        icon="lucide-plus"
        :label="t('program.admin.newProgram')"
        :route="{ name: 'ProgramAdminCreate' }"
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
      :placeholder="t('program.admin.searchPrograms')"
    />

    <div>
      <ListState
        :loading="programs.loading"
        :error="programs.error"
        :empty="empty"
        icon="lucide-graduation-cap"
        :empty-message="search ? t('program.admin.noProgramsFound') : t('program.empty')"
      >
        <template #action>
          <Button
            variant="outline"
            theme="gray"
            icon-left="lucide-plus"
            :label="t('program.admin.createFirst')"
            :route="{ name: 'ProgramAdminCreate' }"
          />
        </template>

        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('program.admin.columns.title') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('program.admin.columns.level') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('program.admin.columns.status') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('program.admin.columns.order') }}</ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('program.admin.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="programs.programs" v-slot="{ item }">
            <ListRow :value="item.id" @click="openProgram(item)">
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
                      ? t('program.admin.form.published')
                      : t('program.admin.form.draft')
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
                  :label="t('program.admin.editProgram')"
                  @click.stop="openProgram(item)"
                />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!programs.loading && !programs.error && !empty"
        :total="programs.total"
        :page="programs.page"
        :per-page="programs.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>
</template>
