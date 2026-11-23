<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Badge, Button, ErrorMessage, dialog, toast } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDate } from '@/shared/format'

import { useContactAdminStore } from '../store'

const { t } = useI18n()
const store = useContactAdminStore()

const gateReady = computed(() => store.checked)
const pageCount = computed(() => Math.max(1, Math.ceil(store.total / store.perPage)))
const hasPrev = computed(() => store.page > 1)
const hasNext = computed(() => store.page < pageCount.value)

onMounted(async () => {
  if (!store.checked) await store.fetchList()
})

async function goTo(nextPage: number) {
  await store.fetchList(nextPage)
}

async function onToggle(item: { id: string; isRead: boolean }) {
  const ok = await store.markRead(item.id, !item.isRead)
  if (ok) {
    item.isRead = !item.isRead
  } else {
    toast.error(store.error)
  }
}

function onDelete(id: string) {
  dialog.danger({
    title: t('contactPage.admin.confirm.title'),
    message: t('contactPage.admin.confirm.message'),
    onConfirm: async () => {
      const ok = await store.remove(id)
      if (ok) {
        toast.success(t('contactPage.admin.toast.deleted'))
        await store.fetchList(store.page)
      } else {
        toast.error(store.error)
      }
    },
  })
}
</script>

<template>
  <ShimmerPage v-if="!gateReady" />
  <div v-else class="mx-auto w-full max-w-5xl p-6">
    <header class="mb-6">
      <h1 class="text-2xl-semibold text-ink-gray-9">{{ t('contactPage.admin.title') }}</h1>
      <p class="mt-1 text-p-sm text-ink-gray-5">{{ t('contactPage.admin.subtitle') }}</p>
    </header>

    <ErrorMessage v-if="store.error" :message="store.error" />

    <div
      v-else-if="!store.messages.length"
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center"
    >
      <p class="text-p-sm text-ink-gray-5">{{ t('contactPage.admin.empty') }}</p>
    </div>

    <List v-else :columns="['minmax(0,1.4fr)', 'minmax(0,1fr)', '7rem', '6rem']">
      <ListHeader>
        <ListHeaderCell>{{ t('contactPage.admin.columns.sender') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('contactPage.admin.columns.message') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('contactPage.admin.columns.received') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('contactPage.admin.columns.actions') }}</ListHeaderCell>
      </ListHeader>
      <ListRows :items="store.messages" v-slot="{ item }">
        <ListRow>
          <ListCell>
            <span class="text-base-medium text-ink-gray-9">{{ item.name }}</span>
            <p class="truncate text-p-sm text-ink-gray-5">{{ item.phone }}</p>
          </ListCell>
          <ListCell>
            <p class="line-clamp-2 text-p-sm text-ink-gray-7">{{ item.message }}</p>
            <Badge
              v-if="item.isRead"
              class="mt-1"
              :label="t('contactPage.admin.read')"
              variant="subtle"
              theme="gray"
            />
          </ListCell>
          <ListCell>
            <span class="text-p-sm text-ink-gray-5">{{ formatDate(item.createdOn) }}</span>
          </ListCell>
          <ListCell>
            <div class="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                theme="gray"
                :label="t(item.isRead ? 'contactPage.admin.actions.unread' : 'contactPage.admin.actions.read')"
                :icon="item.isRead ? 'lucide-mail' : 'lucide-mail-open'"
                @click="onToggle(item)"
              />
              <Button
                variant="ghost"
                size="sm"
                theme="red"
                :label="t('contactPage.admin.actions.delete')"
                icon="lucide-trash-2"
                @click="onDelete(item.id)"
              />
            </div>
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
        :disabled="!hasPrev || store.loading"
        @click="goTo(store.page - 1)"
      />
      <span class="text-p-sm text-ink-gray-4">
        {{ t('shared.pageOf', { page: store.page, total: pageCount }) }}
      </span>
      <Button
        :label="t('shared.nextPage')"
        size="sm"
        variant="subtle"
        icon-right="lucide-arrow-right"
        :disabled="!hasNext || store.loading"
        @click="goTo(store.page + 1)"
      />
    </div>
  </div>
</template>
