<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  PageHeader,
  Spinner,
  Switch,
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
import { formatDate, formatRupiah } from '@/shared/format'

import { TIER_LABELS, useTenancyStore } from '@/features/tenancy/store'
import { featureLabel } from '@/features/tenancy/validation'
import {
  DURATION_UNITS,
  PLAN_TIERS,
  durationLabel,
  usePlansStore,
  type Plan,
  type PlanInput,
} from '../store'

const listColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '120px', '90px'],
  md: ['minmax(0,1fr)', '110px', '120px', '120px', '90px'],
  lg: ['minmax(0,1fr)', '110px', '120px', '120px', '140px', '90px'],
}

const { t } = useI18n()
const tenancy = useTenancyStore()
const store = usePlansStore()
const domainMode = computed(() => tenancy.domainMode('plans'))
const isMaintenance = computed(() => domainMode.value === 'maintenance')
const isDev = computed(() => domainMode.value === 'dev')

// Gate: Plans is superadmin-only; render only once mode is known so
// the catalog never flashes the default before the real mode arrives.
const gateReady = computed(() => tenancy.myOrgsLoaded || tenancy.domainMode('plans') !== '')

const tierOptions = PLAN_TIERS.map((tier) => ({
  label: TIER_LABELS[tier] ?? tier,
  value: tier,
}))

const modeOptions = [
  { label: 'Enabled', value: 'enabled' },
  { label: 'Maintenance (features disabled)', value: 'maintenance' },
  { label: 'Dev (work-in-progress)', value: 'dev' },
]
const modeInput = ref('enabled')
const unitOptions = computed(() =>
  DURATION_UNITS.map((unit) => ({
    label: t(`plans.units.${unit}`),
    value: unit,
  })),
)

const { search, perPage, reload, goToPage } = useListControls({
  fetch: (query) => store.fetchPlans(query),
  setPage: (page) => store.setPage(page),
})

onMounted(() => {
  store.setPage(1)
  reload()
  store.fetchFeatureKeys()
})

// --- create / edit dialog -------------------------------------------------
const formOpen = ref(false)
const editing = ref<Plan | null>(null)
const form = ref({ tier: 'community', durationUnit: 'months', isDefault: false, isActive: true })
const nameInput = ref('')
const durationInput = ref('1')
const priceInput = ref('0')
const featureToggles = ref<Record<string, boolean>>({})
const nameError = ref('')
const durationError = ref('')
const priceError = ref('')

const isCommunity = computed(() => form.value.tier === 'community')
const isDefaultPlan = computed(() => editing.value?.isDefault === true)
const priceDescription = computed(() =>
  isCommunity.value
    ? t('plans.fields.priceCommunity')
    : t('plans.fields.priceProfessional'),
)

const MODE_DOMAINS = ['todo', 'billing', 'plans', 'tenancy', 'infra']

function resetForm(): void {
  nameInput.value = ''
  durationInput.value = '1'
  priceInput.value = '0'
  featureToggles.value = {}
  // Domain mode is GLOBAL per domain (not per-plan): the selected value
  // is stored exactly under the domain that the disabled feature belongs
  // to, and the list in the dialog reflects that global value on reopen.
  modeInput.value = tenancy.domainMode('tenancy')
  nameError.value = ''
  durationError.value = ''
  priceError.value = ''
  store.actionError = ''
}

function openCreate(): void {
  resetForm()
  editing.value = null
  if (!store.featureKeys.length) store.fetchFeatureKeys()
  form.value = {
    tier: 'community',
    durationUnit: 'months',
    isDefault: false,
    isActive: true,
  }
  formOpen.value = true
}

function openEdit(plan: Plan): void {
  resetForm()
  editing.value = plan
  if (!store.featureKeys.length) store.fetchFeatureKeys()
  form.value = {
    tier: plan.tier,
    durationUnit: plan.durationUnit,
    isDefault: plan.isDefault,
    isActive: plan.isActive,
  }
  nameInput.value = plan.name
  durationInput.value = String(plan.durationValue)
  priceInput.value = plan.price == null ? '' : String(plan.price)
  // Seed from the plan's full map, not the registry: if the registry is still
  // loading, delayed toggles must show the stored grants instead of "off".
  featureToggles.value = { ...plan.features }
  formOpen.value = true
}

function onTierChange(value: string | number | null | undefined): void {
  const tier = value ? String(value) : 'community'
  form.value.tier = tier
  // A community plan needs a concrete price; default to free rather than blank.
  if (tier === 'community' && priceInput.value.trim() === '') priceInput.value = '0'
}

async function submit(): Promise<void> {
  if (store.saving) return
  const name = nameInput.value.trim()
  const duration = durationInput.value.trim()
  const price = priceInput.value.trim()

  nameError.value = name ? '' : t('plans.validation.name')
  durationError.value =
    /^\d+$/.test(duration) && Number(duration) >= 1 && Number(duration) <= 3650
      ? ''
      : t('plans.validation.duration')
  priceError.value =
    isCommunity.value && price === ''
      ? t('plans.validation.priceRequired')
      : price === '' || (/^\d+$/.test(price) && Number(price) <= 1_000_000_000)
        ? ''
        : t('plans.validation.price')
  if (nameError.value || durationError.value || priceError.value) return

  const payload: PlanInput = {
    name,
    tier: form.value.tier,
    price: price === '' ? null : Number(price),
    durationValue: Number(duration),
    durationUnit: form.value.durationUnit,
    isDefault: form.value.isDefault,
    isActive: form.value.isActive,
  }
  // Without the registry the toggles are not rendered; omitting the field
  // keeps an existing plan's grants instead of silently clearing them.
  if (!store.featureKeysError && store.featureKeys.length) {
    payload.features = Object.fromEntries(
      store.featureKeys.map((key) => [key, featureToggles.value[key] === true]),
    )
  }

  const saved = editing.value
    ? await store.updatePlan(editing.value.id, payload)
    : await store.createPlan(payload)
  if (!saved) return

  // Domain mode is GLOBAL: pick a mode → it is stored under that
  // domain key (tenancy → tenancy, todo → todo, etc.). Re-saving the
  // same plan does not change its displayed mode unless the operator
  // changed it here (idempotent).
  const MODE_DOMAINS = ['todo', 'billing', 'plans', 'tenancy', 'infra']
  const chosenMode = modeInput.value
  if (MODE_DOMAINS.includes('tenancy') && chosenMode !== tenancy.domainMode('tenancy')) {
    const ok = await tenancy.updateDomainMode('tenancy', chosenMode)
    if (!ok) return
  }

  formOpen.value = false
  toast.success(
    editing.value
      ? t('plans.updated', { name: saved.name })
      : t('plans.created', { name: saved.name }),
  )
}

// --- delete dialog --------------------------------------------------------
const deleteTarget = ref<Plan | null>(null)
const deleteOpen = ref(false)

function openDelete(plan: Plan): void {
  store.actionError = ''
  deleteTarget.value = plan
  deleteOpen.value = true
}

async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value || store.deletingId) return
  const done = await store.deletePlan(deleteTarget.value.id)
  if (!done) return
  const name = deleteTarget.value.name
  deleteOpen.value = false
  toast.success(t('plans.delete.done', { name }))
}
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
    <Badge
      v-if="isDev"
      :label="t('plans.dev')"
      theme="violet"
      variant="subtle"
    />
    <Button
      :label="t('plans.new')"
      icon-left="lucide-plus"
      variant="solid"
      theme="gray"
      @click="openCreate"
    />
  </PageHeader>

  <div
    v-if="!gateReady"
    class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-10"
  >
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-3 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="store.items.length > 0"
      :placeholder="t('plans.searchPlaceholder')"
    />

    <ErrorMessage v-if="store.loadError" :message="store.loadError" />

    <div
      v-if="store.items.length"
      class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2"
    >
      <List class="list-row-px-3" :columns="listColumns">
        <ListHead>
          <ListHeaderCell>{{ t('plans.columns.name') }}</ListHeaderCell>
          <ListHeaderCell class="hidden md:flex">{{ t('plans.columns.tier') }}</ListHeaderCell>
          <ListHeaderCell class="hidden md:flex">{{ t('plans.columns.duration') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('plans.columns.price') }}</ListHeaderCell>
          <ListHeaderCell class="hidden lg:flex">{{ t('plans.columns.status') }}</ListHeaderCell>
          <ListHeaderCell class="justify-end">
            <span class="sr-only">{{ t('plans.columns.actions') }}</span>
          </ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" row-key="id" v-slot="{ item }">
          <ListRow>
            <ListCell class="min-w-0">
              <div class="min-w-0">
                <div class="truncate text-base-medium text-ink-gray-8">
                  {{ item.name }}
                </div>
                <div class="truncate text-p-xs text-ink-gray-5">
                  {{ formatDate(item.createdOn) }}
                </div>
              </div>
            </ListCell>
            <ListCell class="hidden md:flex">
              <Badge
                :label="TIER_LABELS[item.tier] ?? item.tier"
                :theme="item.tier === 'professional' ? 'violet' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="hidden md:flex">
              <span class="text-p-sm text-ink-gray-6">
                {{ durationLabel(item.durationValue, item.durationUnit) }}
              </span>
            </ListCell>
            <ListCell>
              <span class="text-p-sm text-ink-gray-6">
                {{ item.price == null ? t('plans.manual') : formatRupiah(item.price) }}
              </span>
            </ListCell>
            <ListCell class="hidden gap-1 lg:flex">
              <Badge
                v-if="item.isDefault"
                :label="t('plans.default')"
                theme="violet"
                variant="subtle"
              />
              <Badge
                :label="item.isActive ? t('plans.active') : t('plans.inactive')"
                :theme="item.isActive ? 'green' : 'gray'"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="justify-end">
              <div class="flex items-center justify-end gap-1">
                <Button
                  icon="lucide-pencil"
                  variant="ghost"
                  :label="t('plans.edit.title')"
                  @click="openEdit(item)"
                />
                <Button
                  icon="lucide-trash-2"
                  variant="ghost"
                  theme="red"
                  :label="t('plans.delete.title')"
                  @click="openDelete(item)"
                />
              </div>
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
    </div>

    <div
      v-else-if="store.loading"
      class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-10"
    >
      <Spinner />
    </div>

    <div
      v-else-if="store.loadError"
      class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-8"
    >
      <Button
        :label="t('plans.retry')"
        variant="outline"
        icon-left="lucide-refresh-cw"
        @click="reload"
      />
    </div>

    <div
      v-else
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 px-5 py-10 text-center"
    >
      <p class="text-p-sm text-ink-gray-5">
        {{ search ? t('plans.emptySearch') : t('plans.empty') }}
      </p>
      <Button
        v-if="!search"
        class="mt-4"
        :label="t('plans.new')"
        icon-left="lucide-plus"
        variant="solid"
        theme="gray"
        @click="openCreate"
      />
    </div>
  </div>

  <Dialog
    v-model:open="formOpen"
    :title="editing ? t('plans.edit.title') : t('plans.create.title')"
    icon="lucide-layers"
    size="md"
  >
    <template #default>
      <form class="space-y-4" @submit.prevent="submit">
        <ErrorMessage v-if="store.actionError" :message="store.actionError" />
        <FormControl
          v-model="nameInput"
          :label="t('plans.fields.name')"
          :placeholder="t('plans.fields.namePlaceholder')"
          required
          :error="nameError"
        />
        <FormControl
          :model-value="form.tier"
          type="select"
          :label="t('plans.fields.tier')"
          :options="tierOptions"
          :disabled="isDefaultPlan"
          :description="isDefaultPlan ? t('plans.fields.tierLocked') : undefined"
          @update:model-value="onTierChange"
        />
        <div class="grid gap-4 sm:grid-cols-2">
          <FormControl
            v-model="durationInput"
            :label="t('plans.fields.durationValue')"
            placeholder="1"
            required
            :error="durationError"
          />
          <FormControl
            v-model="form.durationUnit"
            type="select"
            :label="t('plans.fields.durationUnit')"
            :options="unitOptions"
          />
        </div>
        <FormControl
          v-model="priceInput"
          :label="t('plans.fields.price')"
          :description="priceDescription"
          :placeholder="isCommunity ? '0' : ''"
          :required="isCommunity"
          :error="priceError"
        />
        <div class="space-y-3 rounded-6 border border-outline-gray-1 p-3">
          <div class="space-y-1">
            <div class="text-p-sm text-ink-gray-7">
              {{ t('plans.featuresTitle') }}
            </div>
            <p class="text-p-xs text-ink-gray-5">
              {{ t('plans.featuresDescription') }}
            </p>
          </div>
          <ErrorMessage v-if="store.featureKeysError" :message="store.featureKeysError" />
          <template v-else>
            <Switch
              v-for="key in store.featureKeys"
              :key="key"
              v-model="featureToggles[key]"
              :label="featureLabel(key)"
            />
          </template>
          <p class="text-p-xs text-ink-gray-5">{{ t('plans.domainModeDescription') }}</p>
          <FormControl
            v-model="modeInput"
            type="select"
            :label="t('plans.domainMode')"
            :options="modeOptions"
          />
        </div>
        <Switch
          v-model="form.isDefault"
          :label="t('plans.fields.isDefault')"
          :description="t('plans.fields.isDefaultDescription')"
          :disabled="isDefaultPlan"
        />
        <Switch
          v-model="form.isActive"
          :label="t('plans.fields.isActive')"
          :description="t('plans.fields.isActiveDescription')"
          :disabled="isDefaultPlan"
        />
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
          :label="editing ? t('plans.edit.submit') : t('plans.create.submit')"
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
    :title="t('plans.delete.title')"
    icon="lucide-trash-2"
    size="sm"
  >
    <div class="space-y-4">
      <p v-if="deleteTarget" class="text-p-sm text-ink-gray-6">
        {{ t('plans.delete.question', { name: deleteTarget.name }) }}
      </p>
      <ErrorMessage v-if="store.actionError" :message="store.actionError" />
    </div>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="close()"
        />
        <Button
          :label="t('plans.delete.confirm')"
          variant="solid"
          theme="red"
          :loading="Boolean(store.deletingId)"
          @click="confirmDelete"
        />
      </div>
    </template>
  </Dialog>
</template>
