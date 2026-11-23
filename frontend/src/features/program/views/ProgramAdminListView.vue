<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Badge, Button, ErrorMessage } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import { useProgramStore } from '../store'

const { t } = useI18n()
const programs = useProgramStore()

const gateReady = computed(() => programs.checked)

onMounted(async () => {
  if (!programs.checked) await programs.fetchAdminList()
})
</script>

<template>
  <ShimmerPage v-if="!gateReady" />
  <div v-else class="mx-auto w-full max-w-5xl p-6">
    <header class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl-semibold text-ink-gray-9">{{ t('program.title') }}</h1>
        <p class="mt-1 text-p-sm text-ink-gray-5">{{ t('program.admin.subtitle') }}</p>
      </div>
      <Button
        :label="t('program.admin.newProgram')"
        variant="solid"
        theme="green"
        icon-left="lucide-plus"
        :route="{ name: 'ProgramAdminCreate' }"
      />
    </header>

    <ErrorMessage v-if="programs.error" :message="programs.error" />

    <div
      v-else-if="!programs.programs.length"
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-10 text-center"
    >
      <p class="text-p-sm text-ink-gray-5">{{ t('program.empty') }}</p>
      <Button
        class="mt-4"
        :label="t('program.admin.createFirst')"
        variant="subtle"
        icon-left="lucide-plus"
        :route="{ name: 'ProgramAdminCreate' }"
      />
    </div>

    <List v-else :columns="['minmax(0,1fr)', '8rem', '7rem', '5rem']">
      <ListHeader>
        <ListHeaderCell>{{ t('program.admin.columns.title') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('program.admin.columns.level') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('program.admin.columns.status') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('program.admin.columns.order') }}</ListHeaderCell>
      </ListHeader>
      <ListRows :items="programs.programs" v-slot="{ item }">
        <ListRow :route="{ name: 'ProgramAdminEdit', params: { slug: item.slug } }">
          <ListCell>
            <span class="text-base-medium text-ink-gray-9">{{ item.title }}</span>
            <p class="truncate text-p-sm text-ink-gray-5">{{ item.excerpt }}</p>
          </ListCell>
          <ListCell>
            <span class="text-p-sm text-ink-gray-6">{{ item.level }}</span>
          </ListCell>
          <ListCell>
            <Badge
              :label="item.status"
              :theme="item.status === 'published' ? 'green' : 'gray'"
              variant="subtle"
            />
          </ListCell>
          <ListCell>
            <span class="text-p-sm text-ink-gray-5">{{ item.order }}</span>
          </ListCell>
        </ListRow>
      </ListRows>
    </List>
  </div>
</template>
