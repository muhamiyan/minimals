<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  FormControl,
  PageHeader,
  Spinner,
  toast,
} from 'frappe-ui'
import type { ListColumnsByBreakpoint } from 'frappe-ui/list'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate, formatRupiah } from '@/shared/format'

import { useAuthStore } from '@/features/auth/store'
import { useBillingStore, type Invoice } from '@/features/billing/store'
import { useGoakalStore, type GoakalTransaction } from '../store'

const listColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '140px'],
  md: ['minmax(0,1fr)', '120px', '130px', '140px'],
  lg: ['minmax(0,1fr)', '120px', '130px', '140px', '140px'],
}

const auth = useAuthStore()
const store = useGoakalStore()
const billing = useBillingStore()
const { t } = useI18n()

const isSuperadmin = computed(() => auth.user?.appRole === 'superadmin')

// Gate: superadmin-only console; render only once myOrgs/listing read is
// ready so the list never flashes the empty default before real data.
const gateReady = computed(() => auth.checked && !store.listLoading && store.settings !== null)

const { search, perPage, reload, goToPage } = useListControls({
  fetch: (query) => store.fetchList(query),
  setPage: (page) => store.setPage(page),
})

onMounted(() => {
  store.setPage(1)
  if (isSuperadmin.value) {
    void reload()
    void store.fetchSettings()
  } else if (auth.checked) {
    void store.fetchSettings()
  }
})

const linkOpen = ref(false)
const linkTx = ref<GoakalTransaction | null>(null)
const linkInvoiceId = ref('')
const linkInvoiceOptions = ref<{ label: string; value: string }[]>([])
const linkInvoiceLoading = ref(false)

async function openLink(tx: GoakalTransaction) {
  if (!isSuperadmin.value) return
  linkTx.value = tx
  linkInvoiceId.value = ''
  linkOpen.value = true
  linkInvoiceLoading.value = true
  try {
    await billing.fetchList({ search: '', perPage: 50, status: 'issued' })
    linkInvoiceOptions.value = billing.items
      .filter((i: Invoice) => i.status === 'issued')
      .map((i: Invoice) => ({ label: `${i.number} · ${i.organizationName}`, value: i.id }))
  } finally {
    linkInvoiceLoading.value = false
  }
}

async function confirmLink() {
  if (!linkTx.value || !linkInvoiceId.value) return
  const ok = await store.linkTransaction(linkTx.value.id, linkInvoiceId.value)
  if (ok) {
    linkOpen.value = false
    toast.success(t('goakal.link.done'))
    await reload()
  }
}

const secretOpen = ref(false)
const secretValue = ref('')

async function confirmSecret() {
  if (!secretValue.value.trim()) return
  const ok = await store.saveSettings(secretValue.value.trim())
  if (ok) {
    secretOpen.value = false
    secretValue.value = ''
    toast.success(t('goakal.settings.done'))
  }
}

function statusTheme(status: string): 'green' | 'blue' | 'gray' {
  if (status === 'PAID') return 'green'
  if (status === 'UNPAID') return 'blue'
  return 'gray'
}
</script>

<template>
  <div class="mx-auto w-full max-w-6xl space-y-3 px-5 py-6">
    <PageHeader :title="t('nav.goakal')" :subtitle="t('goakal.subtitle')">
      <PageBreadcrumbs slot="breadcrumb" />
      <template v-if="isSuperadmin" #actions>
        <Button :label="t('goakal.actions.settings')" @click="secretOpen = true" />
      </template>
    </PageHeader>

    <p class="text-p-sm text-ink-gray-7">{{ t('goakal.description') }}</p>

    <div
      v-if="!gateReady"
      class="flex justify-center rounded-6 border border-outline-gray-1 bg-surface-elevation-2 py-10"
    >
      <Spinner />
    </div>

    <div v-else class="space-y-3">
      <ListToolbar
        v-model:search="search"
        v-model:per-page="perPage"
        :placeholder="t('goakal.filter.search')"
      />

      <ErrorMessage v-if="store.listError" :message="store.listError" />

      <div
        v-if="store.items.length"
        class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2"
      >
        <List class="list-row-px-3" :columns="listColumns">
          <ListHead>
            <ListHeaderCell>{{ t('goakal.columns.payer') }}</ListHeaderCell>
            <ListHeaderCell class="hidden md:flex">{{ t('goakal.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="hidden md:flex">{{ t('goakal.columns.amount') }}</ListHeaderCell>
            <ListHeaderCell class="hidden lg:flex">{{ t('goakal.columns.paidAt') }}</ListHeaderCell>
            <ListHeaderCell class="hidden justify-end md:flex">
              <span class="sr-only">{{ t('goakal.columns.actions') }}</span>
            </ListHeaderCell>
          </ListHead>
          <ListRows :items="store.items" row-key="id" v-slot="{ item }">
          <ListRow>
            <ListCell class="min-w-0">
              <div class="min-w-0">
                <div class="truncate text-base-medium text-ink-gray-8">
                  {{ item.email || item.name || item.externalId }}
                </div>
                <div class="truncate text-p-xs text-ink-gray-5">
                  {{ item.externalId }}
                </div>
              </div>
            </ListCell>
            <ListCell class="hidden md:flex">
              <Badge :label="item.status" :theme="statusTheme(item.status)" variant="subtle" />
            </ListCell>
            <ListCell class="hidden md:flex">
              <span class="text-p-sm text-ink-gray-6">
                {{ item.amount != null ? formatRupiah(item.amount) : '—' }}
              </span>
            </ListCell>
            <ListCell class="hidden lg:flex">
              <span class="text-p-sm text-ink-gray-6">
                {{ item.paidOn ? formatDate(item.paidOn) : '—' }}
              </span>
            </ListCell>
            <ListCell class="hidden justify-end md:flex">
              <Button
                v-if="!item.invoiceId && isSuperadmin"
                variant="ghost"
                :loading="store.linkingId === item.id"
                :label="t('goakal.actions.link')"
                @click="openLink(item)"
              />
              <span v-else-if="item.invoiceId" class="text-p-sm text-ink-gray-6">
                {{ t('goakal.linked') }}
              </span>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
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
      <p class="text-p-sm text-ink-gray-5">{{ t('goakal.empty') }}</p>
    </div>

    <ListFoot
      :total="store.total"
      :page="store.page"
      :per-page="perPage"
      @page="goToPage"
    />
      </div>

    <ErrorMessage v-if="gateReady && store.linkError" :message="store.linkError" />

    <Dialog
      v-model:open="linkOpen"
      :title="t('goakal.link.title')"
      :options="{ width: 'md' }"
    >
      <template #body>
        <div class="flex flex-col gap-4 p-5">
          <Combobox
            v-model="linkInvoiceId"
            :options="linkInvoiceOptions"
            :loading="linkInvoiceLoading"
            :label="t('goakal.link.invoice')"
          />
          <ErrorMessage
            v-if="!linkInvoiceLoading && linkInvoiceOptions.length === 0"
            :message="t('goakal.link.noInvoices')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2 p-5">
          <Button variant="ghost" :label="t('billing.actions.cancel')" @click="linkOpen = false" />
          <Button
            :label="t('goakal.actions.link')"
            :disabled="!linkInvoiceId"
            @click="confirmLink"
          />
        </div>
      </template>
    </Dialog>

    <Dialog
      v-model:open="secretOpen"
      :title="t('goakal.settings.title')"
      :options="{ width: 'md' }"
    >
      <template #body>
        <div class="flex flex-col gap-4 p-5">
          <p class="text-p-sm text-ink-gray-7">{{ t('goakal.settings.description') }}</p>
          <p v-if="store.settings?.configured" class="text-p-sm text-ink-gray-7">
            {{ t('goakal.settings.configured') }}
          </p>
          <FormControl
            v-model="secretValue"
            type="text"
            :label="t('goakal.settings.secret')"
            :placeholder="t('goakal.settings.secretPlaceholder')"
          />
          <ErrorMessage v-if="store.settingsSaveError" :message="store.settingsSaveError" />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2 p-5">
          <Button variant="ghost" :label="t('billing.actions.cancel')" @click="secretOpen = false" />
          <Button
            :label="t('billing.actions.save')"
            :loading="store.settingsSaving"
            :disabled="!secretValue.trim()"
            @click="confirmSecret"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
