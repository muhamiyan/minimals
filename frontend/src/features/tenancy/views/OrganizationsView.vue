<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  PageHeader,
  Spinner,
  toast,
} from 'frappe-ui'
import type { ListColumnsByBreakpoint } from 'frappe-ui/list'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate } from '@/shared/format'

import {
  statusLabel,
  statusTheme,
  tierLabel,
  tierTheme,
  useTenancyStore,
} from '../store'
import { slugify, validateName, validateSlug } from '../validation'

const listColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '110px'],
  md: ['minmax(0,1fr)', '130px', '110px'],
  lg: ['minmax(0,1fr)', '130px', '110px', '90px', '120px'],
}

const router = useRouter()
const { t } = useI18n()
const store = useTenancyStore()

const { search, perPage, reload, goToPage } = useListControls({
  fetch: (query) => store.fetchList(query),
  setPage: (page) => store.setPage(page),
})

// The list state survives navigation; re-entering starts from the first page.
onMounted(() => {
  store.setPage(1)
  reload()
})

// --- create dialog -------------------------------------------------------
const createOpen = ref(false)
const creating = ref(false)
const createName = ref('')
const createSlug = ref('')
const createSlugTouched = ref(false)
const createNameError = ref('')
const createSlugError = ref('')

watch(
  () => createName.value,
  (name) => {
    if (createSlugTouched.value) return
    createSlug.value = slugify(name)
  },
  { flush: 'sync' },
)

function openCreate(): void {
  createName.value = ''
  createSlug.value = ''
  createSlugTouched.value = false
  createNameError.value = ''
  createSlugError.value = ''
  store.createError = ''
  createOpen.value = true
}

function onCreateSlugInput(value: unknown): void {
  createSlug.value = String(value ?? '')
  createSlugTouched.value = true
}

async function submitCreate(): Promise<void> {
  if (creating.value) return
  createNameError.value = validateName(createName.value)
  createSlugError.value = validateSlug(createSlug.value)
  if (createNameError.value || createSlugError.value) return

  creating.value = true
  const org = await store.createOrganization({
    name: createName.value.trim(),
    slug: createSlug.value.trim().toLowerCase(),
  })
  creating.value = false
  if (!org) return

  createOpen.value = false
  toast.success(t('tenancy.console.createdToast', { name: org.name }))
  await router.push({ name: 'TenancyOrg', params: { orgId: org.id } })
}

// --- platform settings dialog ---------------------------------------------
const settingsOpen = ref(false)
const membersLimitInput = ref('')
const membersLimitError = ref('')

async function openSettings(): Promise<void> {
  membersLimitInput.value = ''
  membersLimitError.value = ''
  store.settingsSaveError = ''
  settingsOpen.value = true
  const value = await store.fetchSettings()
  // Prefill only while the dialog is still open — closing mid-fetch must not
  // leak text into the next open (which resets the field anyway).
  if (value !== null && settingsOpen.value) {
    membersLimitInput.value = String(value)
  }
}

async function submitSettings(): Promise<void> {
  if (store.settingsSaving) return
  const raw = membersLimitInput.value.trim()
  membersLimitError.value = /^\d+$/.test(raw)
    ? ''
    : t('tenancy.console.invalidLimit')
  if (membersLimitError.value) return

  const saved = await store.updateMembersLimit(Number(raw))
  if (!saved) return
  settingsOpen.value = false
  toast.success(t('tenancy.console.quotaUpdated'))
}
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
    <div class="flex items-center gap-2">
      <Button
        :label="t('tenancy.console.settings')"
        icon-left="lucide-settings"
        variant="outline"
        @click="openSettings"
      />
      <Button
        :label="t('tenancy.console.newOrg')"
        icon-left="lucide-plus"
        variant="solid"
        theme="gray"
        @click="openCreate"
      />
    </div>
  </PageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-3 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :placeholder="t('tenancy.console.searchPlaceholder')"
    />

    <ErrorMessage v-if="store.listError" :message="store.listError" />

    <div>
      <div v-if="store.listLoading" class="flex justify-center py-10">
        <Spinner />
      </div>

      <div v-else-if="store.listError" class="flex justify-center py-8">
        <Button
          :label="t('tenancy.console.retry')"
          variant="outline"
          icon-left="lucide-refresh-cw"
          @click="reload"
        />
      </div>

      <div
        v-else-if="!store.items.length"
        class="flex flex-col items-center gap-2 py-10 text-center"
      >
        <span class="lucide-building-2 size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">
          {{
            search ? t('tenancy.console.emptySearch') : t('tenancy.console.empty')
          }}
        </p>
        <Button
          v-if="!search"
          :label="t('tenancy.console.newOrg')"
          icon-left="lucide-plus"
          variant="solid"
          theme="gray"
          @click="openCreate"
        />
      </div>

      <template v-else>
        <List class="list-row-px-3" :columns="listColumns">
          <ListHead>
            <ListHeaderCell>{{ t('tenancy.console.name') }}</ListHeaderCell>
            <ListHeaderCell class="hidden md:flex">{{ t('tenancy.console.tier') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('tenancy.console.status') }}</ListHeaderCell>
            <ListHeaderCell class="hidden lg:flex">{{ t('tenancy.console.members') }}</ListHeaderCell>
            <ListHeaderCell class="hidden lg:flex">{{ t('tenancy.console.created') }}</ListHeaderCell>
          </ListHead>
          <ListRows :items="store.items" row-key="id" v-slot="{ item }">
            <ListRow :route="{ name: 'TenancyOrg', params: { orgId: item.id } }">
              <ListCell class="min-w-0">
                <div class="min-w-0">
                  <div class="truncate text-base-medium text-ink-gray-8">
                    {{ item.name }}
                  </div>
                  <div class="truncate text-p-xs text-ink-gray-5">
                    {{ item.slug }}
                  </div>
                </div>
              </ListCell>
              <ListCell class="hidden md:flex">
                <Badge
                  :label="tierLabel(item.subscription)"
                  :theme="tierTheme(item.subscription)"
                  variant="subtle"
                />
              </ListCell>
              <ListCell>
                <Badge
                  :label="statusLabel(item.subscription)"
                  :theme="statusTheme(item.subscription)"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="hidden lg:flex">
                <span class="text-p-sm text-ink-gray-6">{{ item.memberCount }}</span>
              </ListCell>
              <ListCell class="hidden lg:flex">
                <span class="text-p-sm text-ink-gray-5">
                  {{ formatDate(item.createdOn) }}
                </span>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
        <ListFoot
          :total="store.total"
          :page="store.page"
          :per-page="perPage"
          @update:page="goToPage"
        />
      </template>
    </div>
  </div>

  <Dialog
    v-model:open="createOpen"
    :title="t('tenancy.console.create.title')"
    icon="lucide-building-2"
    size="md"
  >
    <template #default>
      <form class="space-y-4" @submit.prevent="submitCreate">
        <ErrorMessage v-if="store.createError" :message="store.createError" />
        <FormControl
          v-model="createName"
          :label="t('tenancy.fields.name')"
          :placeholder="t('tenancy.fields.namePlaceholder')"
          required
          :error="createNameError"
        />
        <FormControl
          :model-value="createSlug"
          :label="t('tenancy.fields.slug')"
          :description="t('tenancy.fields.slugDescription')"
          :placeholder="t('tenancy.fields.slugPlaceholder')"
          required
          :error="createSlugError"
          @update:model-value="onCreateSlugInput"
        />
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="createOpen = false"
        />
        <Button
          :label="t('tenancy.console.create.submit')"
          variant="solid"
          theme="gray"
          :loading="creating"
          @click="submitCreate"
        />
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model:open="settingsOpen"
    :title="t('tenancy.console.settingsTitle')"
    icon="lucide-settings"
    size="md"
  >
    <template #default>
      <form class="space-y-4" @submit.prevent="submitSettings">
        <ErrorMessage v-if="store.settingsError" :message="store.settingsError" />
        <ErrorMessage
          v-if="store.settingsSaveError"
          :message="store.settingsSaveError"
        />
        <div
          v-if="store.settingsLoading && !membersLimitInput"
          class="flex justify-center py-2"
        >
          <Spinner />
        </div>
        <FormControl
          v-model="membersLimitInput"
          :label="t('tenancy.console.membersLimit')"
          :description="t('tenancy.console.membersLimitDescription')"
          placeholder="0"
          required
          :error="membersLimitError"
        />
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="settingsOpen = false"
        />
        <Button
          :label="t('tenancy.console.save')"
          variant="solid"
          theme="gray"
          :loading="store.settingsSaving"
          @click="submitSettings"
        />
      </div>
    </template>
  </Dialog>
</template>
