<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Spinner, dialog, toast } from 'frappe-ui'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate } from '@/shared/format'

import { useContactAdminStore } from '../store'

const { t } = useI18n()
const store = useContactAdminStore()

const gateReady = computed(() => store.checked)
const empty = computed(() => !store.loading && store.messages.length === 0)

const columns = {
  base: ['minmax(0,1.2fr)', 'minmax(0,1fr)', '6rem'],
  md: ['minmax(0,2fr)', 'minmax(0,2fr)', '6.5rem', '6rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  initialPerPage: store.perPage,
  setPage: (page) => {
    store.page = page
  },
  fetch: (query) =>
    store.fetchList({
      search: query.search,
      page: store.page,
      perPage: query.perPage,
    }),
})

async function onToggle(item: { id: string; isRead: boolean }) {
  const ok = await store.markRead(item.id, !item.isRead)
  if (ok) item.isRead = !item.isRead
  else toast.error(store.error)
}

function onDelete(id: string) {
  dialog.danger({
    title: t('contactPage.admin.confirm.title'),
    message: t('contactPage.admin.confirm.message'),
    onConfirm: async () => {
      const ok = await store.remove(id)
      if (ok) {
        toast.success(t('contactPage.admin.toast.deleted'))
        await refresh()
      } else {
        toast.error(store.error)
      }
    },
  })
}

onMounted(async () => {
  await refresh()
})
</script>

<template>
  <AppPageHeader />

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('contactPage.admin.searchMessages')"
    />

    <div>
      <ListState
        :loading="store.loading"
        :error="store.error"
        :empty="empty"
        icon="lucide-mail"
        :empty-message="search ? t('contactPage.admin.noMessagesFound') : t('contactPage.admin.empty')"
      >
        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('contactPage.admin.columns.sender') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('contactPage.admin.columns.message') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('contactPage.admin.columns.received') }}
            </ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('contactPage.admin.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="store.messages" v-slot="{ item }">
            <ListRow :value="item.id">
              <ListCell>
                <div class="flex min-w-0 items-center gap-2">
                  <span class="truncate text-base-medium text-ink-gray-8">
                    {{ item.name }}
                  </span>
                  <span class="truncate text-p-sm text-ink-gray-5">{{ item.phone }}</span>
                </div>
              </ListCell>
              <ListCell>
                <div class="flex min-w-0 items-center gap-2">
                  <span class="truncate text-p-sm text-ink-gray-7">{{ item.message }}</span>
                  <Badge
                    v-if="item.isRead"
                    :label="t('contactPage.admin.read')"
                    variant="subtle"
                    theme="gray"
                  />
                </div>
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="truncate text-p-sm text-ink-gray-5">
                  {{ formatDate(item.createdOn) }}
                </span>
              </ListCell>
              <ListCell>
                <div class="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    theme="gray"
                    icon="lucide-mail-open"
                    :label="t(item.isRead ? 'contactPage.admin.actions.unread' : 'contactPage.admin.actions.read')"
                    @click="onToggle(item)"
                  />
                  <Button
                    variant="ghost"
                    theme="red"
                    icon="lucide-trash-2"
                    :label="t('contactPage.admin.actions.delete')"
                    @click="onDelete(item.id)"
                  />
                </div>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!store.loading && !store.error && !empty"
        :total="store.total"
        :page="store.page"
        :per-page="store.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>
</template>
