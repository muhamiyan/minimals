<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  Badge,
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  PageHeader,
  Select,
  Spinner,
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

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import InvoicePrintDialog from '../components/InvoicePrintDialog.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate, formatRupiah } from '@/shared/format'

import { useAuthStore } from '@/features/auth/store'
import { TIER_LABELS, useTenancyStore } from '@/features/tenancy/store'
import {
  invoiceStatusLabel,
  invoiceStatusTheme,
  nextPeriodStart,
  useBillingStore,
  type BillingSettings,
  type Invoice,
  type OrgOption,
} from '../store'

// base: Invoice, Amount — md: + Status, Actions — lg: + Period, Due
const listColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '120px'],
  md: ['minmax(0,1fr)', '130px', '120px', '150px'],
  lg: ['minmax(0,1fr)', '130px', '150px', '110px', '120px', '150px'],
}

const auth = useAuthStore()
const tenancy = useTenancyStore()
const store = useBillingStore()
const router = useRouter()
const { t } = useI18n()

const isSuperadmin = computed(() => auth.user?.appRole === 'superadmin')
const domainMode = computed(() => tenancy.domainMode('billing'))
const isMaintenance = computed(() => domainMode.value === 'maintenance')
const isDev = computed(() => domainMode.value === 'dev')

const statusFilter = ref('')
const orgFilter = ref('')

const statusOptions = computed(() => [
  { label: t('billing.status.all'), value: '' },
  { label: t('billing.status.issued'), value: 'issued' },
  { label: t('billing.status.paid'), value: 'paid' },
  { label: t('billing.status.void'), value: 'void' },
])

const orgChoices = computed(() => {
  if (isSuperadmin.value) return store.orgOptions
  // Owners are scoped server-side; their filter options come from my orgs.
  return tenancy.myOrgs
    .filter((org) => org.myRole === 'owner')
    .map((org) => ({ id: org.id, name: org.name }))
})

const orgSelectOptions = computed(() => [
  { label: t('billing.filter.allOrgs'), value: '' },
  ...orgChoices.value.map((org) => ({ label: org.name, value: org.id })),
])

const { search, perPage, reload, goToPage } = useListControls({
  fetch: (query) =>
    store.fetchList({
      ...query,
      status: statusFilter.value,
      orgId: orgFilter.value,
    }),
  setPage: (page) => store.setPage(page),
})

onMounted(() => {
  store.setPage(1)
  if (isSuperadmin.value) store.fetchOrgOptions()
  if (!isSuperadmin.value && !tenancy.myOrgsLoaded) return
  const activeOrgId = tenancy.currentOrg?.id
  if (!isSuperadmin.value && activeOrgId) {
    if (!orgChoices.value.some((org) => org.id === activeOrgId)) {
      router.replace({ name: 'Dashboard' })
      return
    }
    orgFilter.value = activeOrgId
  }
  reload()
})

watch(
  () => tenancy.myOrgsLoaded,
  (loaded) => {
    if (isSuperadmin.value || !loaded) return
    const activeOrgId = tenancy.currentOrg?.id
    if (!activeOrgId) return
    if (!orgChoices.value.some((org) => org.id === activeOrgId)) {
      router.replace({ name: 'Dashboard' })
      return
    }
    orgFilter.value = activeOrgId
    store.setPage(1)
    reload()
  },
)

watch(
  () => tenancy.currentOrg?.id,
  (orgId) => {
    if (isSuperadmin.value || !orgId) return
    if (!tenancy.myOrgsLoaded) return
    if (!orgChoices.value.some((org) => org.id === orgId)) {
      router.replace({ name: 'Dashboard' })
      return
    }
    if (orgFilter.value === orgId) return
    orgFilter.value = orgId
    store.setPage(1)
    reload()
  },
)

function onStatusFilter(value: SelectOptionValue | null | undefined): void {
  statusFilter.value = value ? String(value) : ''
  store.setPage(1)
  reload()
}

function onOrgFilter(value: SelectOptionValue | null | undefined): void {
  orgFilter.value = value ? String(value) : ''
  store.setPage(1)
  reload()
}

// --- print dialog --------------------------------------------------------
const printInvoice = ref<Invoice | null>(null)
const printOpen = ref(false)

function openPrint(invoice: Invoice): void {
  printInvoice.value = invoice
  printOpen.value = true
}

// --- pay / void dialogs --------------------------------------------------
const payTarget = ref<Invoice | null>(null)
const payOpen = ref(false)
const payAmountInput = ref('')
const payAmountError = ref('')
const voidTarget = ref<Invoice | null>(null)
const voidOpen = ref(false)

function openPay(invoice: Invoice): void {
  store.actionError = ''
  payTarget.value = invoice
  payAmountInput.value = String(invoice.amount)
  payAmountError.value = ''
  payOpen.value = true
}

async function submitPay(): Promise<void> {
  if (!payTarget.value || store.actingId) return
  const amount = payAmountInput.value.trim()
  payAmountError.value =
    amount === '' || /^\d+$/.test(amount) ? '' : t('billing.validation.amount')
  if (payAmountError.value) return
  const done = await store.markPaid(
    payTarget.value.id,
    amount === '' ? undefined : Number(amount),
  )
  if (!done) return
  payOpen.value = false
  toast.success(t('billing.pay.done', { number: payTarget.value.number }))
}

function openVoid(invoice: Invoice): void {
  store.actionError = ''
  voidTarget.value = invoice
  voidOpen.value = true
}

async function submitVoid(): Promise<void> {
  if (!voidTarget.value || store.actingId) return
  const done = await store.voidInvoice(voidTarget.value.id)
  if (!done) return
  voidOpen.value = false
  toast.success(t('billing.void.done', { number: voidTarget.value.number }))
}

// --- create invoice dialog ------------------------------------------------
const createOpen = ref(false)
const createOrgId = ref('')
const createOrgQuery = ref('')
/** Holds the selected org's label while server results change with the query. */
const createOrgSelection = ref<OrgOption | null>(null)
const createPeriodStart = ref('')
const createAmountInput = ref('')
const createOrgError = ref('')
const createPeriodError = ref('')
const createAmountError = ref('')

function orgOptionLabel(org: OrgOption): string {
  const tier = org.tier ? (TIER_LABELS[org.tier] ?? org.tier) : ''
  return tier ? `${org.name} (${tier})` : org.name
}

const createOrgChoices = computed(() => {
  const options = store.orgSearchResults.map((org) => ({
    label: orgOptionLabel(org),
    value: org.id,
  }))
  const selected = createOrgSelection.value
  if (selected && !options.some((option) => option.value === selected.id)) {
    options.unshift({ label: orgOptionLabel(selected), value: selected.id })
  }
  return options
})

let orgSearchTimer: ReturnType<typeof setTimeout> | undefined

watch(createOrgQuery, (query) => {
  clearTimeout(orgSearchTimer)
  orgSearchTimer = undefined
  // Picking an option (or closing the popover) writes the selected label into
  // the bound query; that is not a search.
  const selected = createOrgSelection.value
  if (selected && query === orgOptionLabel(selected)) return
  orgSearchTimer = setTimeout(() => {
    orgSearchTimer = undefined
    void store.searchOrgOptions(query)
  }, 250)
})

// Once the query is bound the combobox keeps it; reset on open so the list
// shows the unfiltered first page again.
function onCreateOrgOpen(open: boolean): void {
  if (!open) return
  if (createOrgQuery.value) {
    createOrgQuery.value = '' // the watcher loads the first page
    return
  }
  void store.searchOrgOptions('')
}

function selectCreateOrg(orgId: string, org: OrgOption | null = null): void {
  createOrgId.value = orgId
  createOrgSelection.value =
    org ?? store.orgOptions.find((option) => option.id === orgId) ?? null
  createPeriodStart.value = nextPeriodStart(
    createOrgSelection.value?.startedOn ?? null,
    createOrgSelection.value?.durationValue ?? 1,
    createOrgSelection.value?.durationUnit ?? 'months',
  )
}

const createAmountDescription = computed(() =>
  createOrgSelection.value?.planPrice == null
    ? t('billing.create.amountRequired')
    : t('billing.create.amountDescription'),
)

function openCreate(): void {
  store.createError = ''
  createOrgError.value = ''
  createPeriodError.value = ''
  createAmountError.value = ''
  createAmountInput.value = ''
  createOrgQuery.value = ''
  const first = store.orgOptions[0] ?? null
  selectCreateOrg(first?.id ?? '', first)
  createOpen.value = true
}

function onCreateOrg(value: string | number | null | undefined): void {
  createOrgError.value = ''
  if (value === null || value === undefined || value === '') {
    createOrgId.value = ''
    createOrgSelection.value = null
    return
  }
  const orgId = String(value)
  const org =
    store.orgSearchResults.find((option) => option.id === orgId) ??
    store.orgOptions.find((option) => option.id === orgId) ??
    null
  selectCreateOrg(orgId, org)
}

async function submitCreate(): Promise<void> {
  if (store.creatingInvoice) return
  const amount = createAmountInput.value.trim()
  createOrgError.value = createOrgId.value ? '' : t('billing.validation.org')
  createPeriodError.value = createPeriodStart.value
    ? ''
    : t('billing.validation.period')
  createAmountError.value =
    amount === '' || /^\d+$/.test(amount) ? '' : t('billing.validation.amount')
  if (createOrgError.value || createPeriodError.value || createAmountError.value) return

  const invoice = await store.createInvoice({
    organizationId: createOrgId.value,
    periodStart: createPeriodStart.value,
    ...(amount === '' ? {} : { amount: Number(amount) }),
  })
  if (!invoice) return

  createOpen.value = false
  toast.success(t('billing.create.done', { number: invoice.number }))
  store.setPage(1)
  reload()
}

// --- billing settings dialog ---------------------------------------------
const settingsOpen = ref(false)
const settingsOriginal = ref<BillingSettings | null>(null)
const trialDaysInput = ref('')
const leadDaysInput = ref('')
const trialDaysError = ref('')
const leadDaysError = ref('')

async function openSettings(): Promise<void> {
  settingsOriginal.value = null
  trialDaysInput.value = ''
  leadDaysInput.value = ''
  trialDaysError.value = ''
  leadDaysError.value = ''
  store.settingsSaveError = ''
  settingsOpen.value = true
  const value = await store.fetchSettings()
  // Prefill only while the dialog is still open — closing mid-fetch must not
  // leak text into the next open (which resets the fields anyway).
  if (value !== null && settingsOpen.value) {
    settingsOriginal.value = value
    trialDaysInput.value = String(value.trialDays)
    leadDaysInput.value = String(value.invoiceLeadDays)
  }
}

async function submitSettings(): Promise<void> {
  if (store.settingsSaving) return
  const trial = trialDaysInput.value.trim()
  const lead = leadDaysInput.value.trim()
  const invalidDays = t('billing.validation.days')
  trialDaysError.value = /^\d+$/.test(trial) ? '' : invalidDays
  leadDaysError.value = /^\d+$/.test(lead) ? '' : invalidDays
  if (trialDaysError.value || leadDaysError.value) return

  // Send only edited fields: the API updates partially, so a concurrent
  // change to an untouched setting is never overwritten.
  const original = settingsOriginal.value
  const next: BillingSettings = {
    trialDays: Number(trial),
    invoiceLeadDays: Number(lead),
  }
  const changes: Partial<BillingSettings> = {}
  for (const field of Object.keys(next) as (keyof BillingSettings)[]) {
    if (!original || next[field] !== original[field]) changes[field] = next[field]
  }
  if (!Object.keys(changes).length) {
    settingsOpen.value = false
    return
  }

  const saved = await store.saveSettings(changes)
  if (!saved) return
  settingsOpen.value = false
  toast.success(t('billing.settings.done'))
}
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
    <Badge
      v-if="isDev"
      :label="t('billing.dev')"
      theme="violet"
      variant="subtle"
    />
    <div v-if="isSuperadmin && !isMaintenance" class="flex items-center gap-2">
      <Button
        :label="t('billing.actions.settings')"
        icon-left="lucide-settings"
        variant="outline"
        @click="openSettings"
      />
      <Button
        :label="t('billing.actions.create')"
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
      :show-per-page="store.items.length > 0"
      :placeholder="t('billing.filter.search')"
    >
      <Select
        :model-value="statusFilter"
        :options="statusOptions"
        class="w-40"
        @update:model-value="onStatusFilter"
      />
      <Select
        :model-value="orgFilter"
        :options="orgSelectOptions"
        class="w-52"
        @update:model-value="onOrgFilter"
      />
    </ListToolbar>

    <ErrorMessage v-if="store.listError" :message="store.listError" />

    <div
      v-if="store.items.length"
      class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2"
    >
      <List class="list-row-px-3" :columns="listColumns">
        <ListHead>
          <ListHeaderCell>{{ t('billing.columns.invoice') }}</ListHeaderCell>
          <ListHeaderCell class="hidden md:flex">
            {{ t('billing.columns.status') }}
          </ListHeaderCell>
          <ListHeaderCell class="hidden lg:flex">
            {{ t('billing.columns.period') }}
          </ListHeaderCell>
          <ListHeaderCell class="hidden lg:flex">
            {{ t('billing.columns.due') }}
          </ListHeaderCell>
          <ListHeaderCell>{{ t('billing.columns.amount') }}</ListHeaderCell>
          <ListHeaderCell class="hidden justify-end md:flex">
            <span class="sr-only">{{ t('billing.columns.actions') }}</span>
          </ListHeaderCell>
        </ListHead>
        <ListRows :items="store.items" row-key="id" v-slot="{ item }">
          <ListRow>
            <ListCell class="min-w-0">
              <div class="min-w-0">
                <div class="truncate text-base-medium text-ink-gray-8">
                  {{ item.number }}
                </div>
                <div class="truncate text-p-xs text-ink-gray-5">
                  {{ item.organizationName || item.tier }}
                </div>
              </div>
            </ListCell>
            <ListCell class="hidden md:flex">
              <Badge
                :label="invoiceStatusLabel(item.status)"
                :theme="invoiceStatusTheme(item.status)"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="hidden lg:flex">
              <span class="text-p-sm text-ink-gray-6">
                {{ formatDate(item.periodStart) }}
              </span>
            </ListCell>
            <ListCell class="hidden lg:flex">
              <span class="text-p-sm text-ink-gray-6">
                {{ formatDate(item.dueOn) }}
              </span>
            </ListCell>
            <ListCell>
              <span class="text-base-medium text-ink-gray-8">
                {{ formatRupiah(item.amount) }}
              </span>
            </ListCell>
            <ListCell class="hidden justify-end md:flex">
              <div class="flex items-center justify-end gap-1">
                <Button
                  icon="lucide-printer"
                  :label="t('billing.actions.print')"
                  variant="ghost"
                  @click="openPrint(item)"
                />
                <template v-if="isSuperadmin && item.status === 'issued'">
                  <Button
                    icon="lucide-check"
                    :label="t('billing.actions.markPaid')"
                    variant="ghost"
                    :loading="store.actingId === item.id"
                    @click="openPay(item)"
                  />
                  <Button
                    icon="lucide-ban"
                    :label="t('billing.actions.void')"
                    variant="ghost"
                    theme="red"
                    :loading="store.actingId === item.id"
                    @click="openVoid(item)"
                  />
                </template>
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
      v-else-if="store.listLoading"
      class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-10"
    >
      <Spinner />
    </div>

    <div
      v-else-if="store.listError"
      class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-8"
    >
      <Button
        :label="t('billing.actions.retry')"
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
        {{
          search || statusFilter || orgFilter
            ? t('billing.empty.filtered')
            : t('billing.empty.none')
        }}
      </p>
      <Button
        v-if="isSuperadmin && !search && !statusFilter && !orgFilter"
        class="mt-4"
        :label="t('billing.actions.create')"
        icon-left="lucide-plus"
        variant="solid"
        theme="gray"
        @click="openCreate"
      />
    </div>
  </div>

  <InvoicePrintDialog v-model:open="printOpen" :invoice="printInvoice" />

  <Dialog
    v-model:open="payOpen"
    :title="t('billing.pay.title')"
    icon="lucide-check-circle-2"
    size="sm"
  >
    <div class="space-y-4">
      <p v-if="payTarget" class="text-p-sm text-ink-gray-6">
        {{
          t('billing.pay.question', {
            number: payTarget.number,
            amount: formatRupiah(payTarget.amount),
          })
        }}
      </p>
      <FormControl
        v-model="payAmountInput"
        :label="t('billing.pay.amount')"
        :description="t('billing.pay.amountDescription')"
        :error="payAmountError"
      />
      <ErrorMessage v-if="store.actionError" :message="store.actionError" />
    </div>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button
          :label="t('billing.actions.cancel')"
          variant="outline"
          @click="close()"
        />
        <Button
          :label="t('billing.actions.markPaid')"
          variant="solid"
          theme="gray"
          :loading="Boolean(store.actingId)"
          @click="submitPay"
        />
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model:open="voidOpen"
    :title="t('billing.void.title')"
    icon="lucide-ban"
    size="sm"
  >
    <div class="space-y-4">
      <p v-if="voidTarget" class="text-p-sm text-ink-gray-6">
        {{ t('billing.void.question', { number: voidTarget.number }) }}
      </p>
      <ErrorMessage v-if="store.actionError" :message="store.actionError" />
    </div>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button
          :label="t('billing.actions.cancel')"
          variant="outline"
          @click="close()"
        />
        <Button
          :label="t('billing.void.confirm')"
          variant="solid"
          theme="red"
          :loading="Boolean(store.actingId)"
          @click="submitVoid"
        />
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model:open="createOpen"
    :title="t('billing.create.title')"
    icon="lucide-file-plus"
    size="md"
  >
    <template #default>
      <form class="space-y-4" @submit.prevent="submitCreate">
        <ErrorMessage v-if="store.createError" :message="store.createError" />
        <Combobox
          :model-value="createOrgId || null"
          :options="createOrgChoices"
          :filterable="false"
          :loading="store.orgSearchLoading"
          v-model:query="createOrgQuery"
          :label="t('billing.create.org')"
          :description="t('billing.create.orgDescription')"
          :placeholder="t('billing.create.orgPlaceholder')"
          :empty-text="t('billing.create.orgEmpty')"
          required
          :error="createOrgError"
          @update:model-value="onCreateOrg"
          @update:open="onCreateOrgOpen"
        />
        <FormControl
          v-model="createPeriodStart"
          type="date"
          :label="t('billing.create.period')"
          :description="t('billing.create.periodDescription')"
          required
          :error="createPeriodError"
        />
        <FormControl
          v-model="createAmountInput"
          :label="t('billing.create.amount')"
          :description="createAmountDescription"
          :error="createAmountError"
        />
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('billing.actions.cancel')"
          variant="outline"
          @click="createOpen = false"
        />
        <Button
          :label="t('billing.actions.create')"
          variant="solid"
          theme="gray"
          :loading="store.creatingInvoice"
          @click="submitCreate"
        />
      </div>
    </template>
  </Dialog>

  <Dialog
    v-model:open="settingsOpen"
    :title="t('billing.settings.title')"
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
        <div v-if="store.settingsLoading && !trialDaysInput" class="flex justify-center py-2">
          <Spinner />
        </div>
        <FormControl
          v-model="trialDaysInput"
          :label="t('billing.settings.trial')"
          :description="t('billing.settings.trialDescription')"
          placeholder="30"
          required
          :error="trialDaysError"
        />
        <FormControl
          v-model="leadDaysInput"
          :label="t('billing.settings.lead')"
          :description="t('billing.settings.leadDescription')"
          placeholder="7"
          required
          :error="leadDaysError"
        />
      </form>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('billing.actions.cancel')"
          variant="outline"
          @click="settingsOpen = false"
        />
        <Button
          :label="t('billing.actions.save')"
          variant="solid"
          theme="gray"
          :loading="store.settingsSaving"
          @click="submitSettings"
        />
      </div>
    </template>
  </Dialog>
</template>
