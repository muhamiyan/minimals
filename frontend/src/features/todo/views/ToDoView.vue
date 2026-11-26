<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Select,
  Spinner,
  Switch,
  toast,
  type SelectOptionValue,
} from 'frappe-ui'
import type { ListColumnsByBreakpoint } from 'frappe-ui/list'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListRowOpenButton from '@/shared/components/ListRowOpenButton.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate } from '@/shared/format'
import { LIST_ROW_SURFACE_CLASS } from '@/shared/listRow'

import { useTenancyStore } from '@/features/tenancy/store'
import {
  useTodoStore,
  type Todo,
  type TodoStatusFilter,
} from '../store'

const listColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '110px', '80px'],
  md: ['minmax(0,1fr)', '110px', '120px', '110px'],
}

const { t } = useI18n()
const tenancy = useTenancyStore()
const store = useTodoStore()

const org = computed(() => tenancy.currentOrg)
const featureOn = computed(() => tenancy.hasFeature('todo'))
const domainMode = computed(() => tenancy.domainMode('todo'))
const disabledReasonTitle = computed(() => {
  if (domainMode.value === 'maintenance') return t('todo.maintenance')
  if (domainMode.value === 'dev') return t('todo.dev')
  return t('todo.upsell.title')
})
const disabledReasonHint = computed(() => {
  if (domainMode.value === 'maintenance') return t('todo.maintenanceHint')
  if (domainMode.value === 'dev') return t('todo.devHint')
  return t('todo.upsell.description')
})

// Gate: show nothing until features+mode are known (no flash of the
// default upsell banner before the checks resolve).
const gateReady = computed(
  () => tenancy.myOrgsLoaded && (tenancy.activeFeaturesLoading === false),
)

const status = ref<TodoStatusFilter>('all')
const statusOptions = computed(() => [
  { label: t('todo.filter.all'), value: 'all' },
  { label: t('todo.filter.open'), value: 'open' },
  { label: t('todo.filter.done'), value: 'done' },
])

const { search, perPage, reload, goToPage } = useListControls({
  fetch: (query) => {
    const orgId = org.value?.id
    if (orgId) store.list(orgId, { ...query, completed: status.value })
  },
  setPage: (page) => store.setPage(page),
})

const isFiltered = computed(
  () => search.value.trim() !== '' || status.value !== 'all',
)

const empty = computed(
  () => !store.loading && store.items.length === 0,
)

function onStatusChange(value: SelectOptionValue | null | undefined): void {
  status.value = value === 'open' || value === 'done' ? value : 'all'
  store.setPage(1)
  reload()
}

onMounted(() => {
  if (!tenancy.myOrgsLoaded) tenancy.fetchMyOrgs()
  tenancy.fetchDomainModes()
})

// Feature flags resolve per organization: reset first so rows from the
// previous organization are never shown while the next request is pending.
watch(
  () => org.value?.id ?? null,
  async (orgId) => {
    store.reset()
    if (!orgId) return
    await tenancy.fetchActiveFeatures()
    if (tenancy.hasFeature('todo')) reload()
  },
  { immediate: true },
)

async function retryFeatures(): Promise<void> {
  await tenancy.fetchActiveFeatures()
  if (tenancy.hasFeature('todo')) {
    store.setPage(1)
    reload()
  }
}

// --- create / edit dialog -------------------------------------------------
const formOpen = ref(false)
const editing = ref<Todo | null>(null)
const form = ref({ title: '', description: '', completed: false, dueDate: '' })
const titleError = ref('')

function openCreate(): void {
  if (!featureOn.value) return
  editing.value = null
  form.value = { title: '', description: '', completed: false, dueDate: '' }
  titleError.value = ''
  store.error = ''
  formOpen.value = true
}

function openEdit(todo: Todo): void {
  editing.value = todo
  form.value = {
    title: todo.title,
    description: todo.description ?? '',
    completed: todo.completed,
    dueDate: todo.dueDate ?? '',
  }
  titleError.value = ''
  store.error = ''
  formOpen.value = true
}

async function submit(): Promise<void> {
  if (store.saving || !org.value) return
  const title = form.value.title.trim()
  titleError.value = title ? '' : t('todo.validation.title')
  if (titleError.value) return

  const payload = {
    title,
    description: form.value.description.trim() || null,
    completed: form.value.completed,
    dueDate: form.value.dueDate || null,
  }
  const saved = editing.value
    ? await store.update(org.value.id, editing.value.id, payload)
    : await store.create(org.value.id, payload)
  if (!saved) return

  formOpen.value = false
  toast.success(editing.value ? t('todo.updated') : t('todo.created'))
}

async function toggle(todo: Todo): Promise<void> {
  if (!org.value || store.saving) return
  await store.update(org.value.id, todo.id, { completed: !todo.completed })
}

// --- delete dialog --------------------------------------------------------
const deleteTarget = ref<Todo | null>(null)
const deleteOpen = ref(false)

function openDelete(todo: Todo): void {
  store.error = ''
  deleteTarget.value = todo
  deleteOpen.value = true
}

async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value || !org.value || store.deletingId) return
  const done = await store.remove(org.value.id, deleteTarget.value.id)
  if (!done) return
  deleteOpen.value = false
  toast.success(t('todo.delete.done'))
}
</script>

<template>
  <AppPageHeader>
    <template #actions>
      <Button
        v-if="featureOn && gateReady"
        :label="t('todo.new')"
        icon-left="lucide-plus"
        variant="solid"
        theme="gray"
        @click="openCreate"
      />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div v-if="!org" class="py-10 text-center text-p-sm text-ink-gray-5">
      {{ t('todo.noOrgFeature') }}
    </div>

    <div v-else-if="tenancy.activeFeaturesLoading" class="flex justify-center py-10">
      <Spinner />
    </div>

    <div v-else-if="tenancy.activeFeaturesError" class="space-y-4">
      <ErrorMessage :message="tenancy.activeFeaturesError" />
      <Button
        :label="t('todo.retry')"
        variant="outline"
        icon-left="lucide-refresh-cw"
        @click="retryFeatures"
      />
    </div>

    <div
      v-else-if="!featureOn"
      class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-6"
    >
      <div class="text-base-medium text-ink-gray-8">{{ disabledReasonTitle }}</div>
      <p class="text-p-sm text-ink-gray-5">{{ disabledReasonHint }}</p>
    </div>

    <template v-else>
      <ListToolbar
        v-model:search="search"
        v-model:per-page="perPage"
        :show-per-page="!empty"
        :placeholder="t('todo.searchPlaceholder')"
      >
        <Select
          :model-value="status"
          :options="statusOptions"
          class="w-36"
          @update:model-value="onStatusChange"
        />
      </ListToolbar>

      <div>
        <ListState
          :loading="store.loading"
          :error="store.listError"
          :empty="empty"
          icon="lucide-list-todo"
          :empty-message="isFiltered ? t('todo.emptyFiltered') : t('todo.empty')"
        >
        <List class="list-row-px-3" :columns="listColumns">
          <ListHead>
            <ListHeaderCell>{{ t('todo.columns.title') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('todo.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="hidden md:flex">{{ t('todo.columns.due') }}</ListHeaderCell>
            <ListHeaderCell class="justify-end">
              <span class="sr-only">{{ t('todo.columns.actions') }}</span>
            </ListHeaderCell>
          </ListHead>
          <ListRows :items="store.items" row-key="id" v-slot="{ item }">
            <ListRow :class="LIST_ROW_SURFACE_CLASS">
              <ListCell class="min-w-0">
                <ListRowOpenButton
                  :label="`${t('todo.edit.title')}: ${item.title}`"
                  @click="openEdit(item)"
                />
                <div class="min-w-0">
                  <div
                    class="truncate text-base-medium"
                    :class="item.completed ? 'text-ink-gray-4 line-through' : 'text-ink-gray-8'"
                  >
                    {{ item.title }}
                  </div>
                  <div v-if="item.description" class="truncate text-p-xs text-ink-gray-5">
                    {{ item.description }}
                  </div>
                </div>
              </ListCell>
              <ListCell>
                <Badge
                  :label="item.completed ? t('todo.status.done') : t('todo.status.open')"
                  :theme="item.completed ? 'green' : 'amber'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="hidden md:flex">
                <span class="text-p-sm text-ink-gray-6">
                  {{ item.dueDate ? formatDate(item.dueDate) : '—' }}
                </span>
              </ListCell>
              <ListCell class="justify-end">
                <div class="flex items-center justify-end gap-1">
                  <Button
                    icon="lucide-check"
                    variant="ghost"
                    class="relative"
                    :label="item.completed ? t('todo.actions.reopen') : t('todo.actions.complete')"
                    @click="toggle(item)"
                  />
                  <Button
                    icon="lucide-pencil"
                    variant="ghost"
                    class="relative"
                    :label="t('todo.actions.edit')"
                    @click="openEdit(item)"
                  />
                  <Button
                    icon="lucide-trash-2"
                    variant="ghost"
                    theme="red"
                    class="relative"
                    :label="t('todo.actions.delete')"
                    @click="openDelete(item)"
                  />
                </div>
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
        </ListState>
        <ListFoot
          v-if="!store.loading && !store.listError && store.items.length"
          :total="store.total"
          :page="store.page"
          :per-page="perPage"
          @update:page="goToPage"
        />
      </div>
    </template>
  </div>

  <Dialog
    v-model:open="formOpen"
    :title="editing ? t('todo.edit.title') : t('todo.create.title')"
    icon="lucide-list-todo"
    size="md"
  >
    <template #default>
      <form class="space-y-4" @submit.prevent="submit">
        <ErrorMessage v-if="store.error" :message="store.error" />
        <FormControl
          v-model="form.title"
          :label="t('todo.fields.title')"
          :placeholder="t('todo.fields.titlePlaceholder')"
          required
          :error="titleError"
        />
        <FormControl
          v-model="form.description"
          type="textarea"
          :label="t('todo.fields.description')"
          :placeholder="t('todo.fields.descriptionPlaceholder')"
        />
        <div class="grid gap-4 sm:grid-cols-2">
          <FormControl
            v-model="form.dueDate"
            type="date"
            :label="t('todo.fields.dueDate')"
            clearable
          />
          <div class="space-y-1.5">
            <label
              for="todo-completed"
              class="block text-sm leading-tighter text-ink-gray-6"
            >
              {{ t('todo.fields.completed') }}
            </label>
            <div class="flex h-7 items-center">
              <Switch id="todo-completed" v-model="form.completed" />
            </div>
          </div>
        </div>
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="formOpen = false"
        />
        <Button
          :label="editing ? t('todo.edit.submit') : t('todo.create.submit')"
          variant="solid"
          theme="gray"
          :loading="store.saving"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model:open="deleteOpen"
    :title="t('todo.delete.title')"
    icon="lucide-trash-2"
    size="sm"
  >
    <div class="space-y-4">
      <p v-if="deleteTarget" class="text-p-sm text-ink-gray-6">
        {{ t('todo.delete.question', { title: deleteTarget.title }) }}
      </p>
      <ErrorMessage v-if="store.error" :message="store.error" />
    </div>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="close()"
        />
        <Button
          :label="t('todo.delete.confirm')"
          variant="solid"
          theme="red"
          :loading="Boolean(store.deletingId)"
          @click="confirmDelete"
        />
      </div>
    </template>
  </Dialog>
</template>
