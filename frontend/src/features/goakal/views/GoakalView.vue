<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Button,
  Combobox,
  Dialog,
  ErrorMessage,
  Spinner,
  TextInput,
  toast,
} from 'frappe-ui'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate, formatRupiah } from '@/shared/format'

import { useAuthStore } from '@/features/auth/store'
import { useBillingStore, type Invoice } from '@/features/billing/store'
import { useGoakalStore, type GoakalTransaction } from '../store'

// base: Payer, Status, Actions — md: + Amount, Paid at
const columns = {
  base: ['minmax(0,1fr)', '6rem', '6rem'],
  md: ['minmax(0,2fr)', '6rem', '7rem', '9rem', '6rem'],
}

const auth = useAuthStore()
const store = useGoakalStore()
const billing = useBillingStore()
const { t } = useI18n()

const isSuperadmin = computed(() => auth.user?.appRole === 'superadmin')

const initialLoaded = ref(false)
const gateReady = computed(() => auth.checked && initialLoaded.value)

const empty = computed(() => !store.listLoading && store.items.length === 0)

const { search, perPage, reload, goToPage } = useListControls({
  setPage: (page) => store.setPage(page),
  fetch: (query) => store.fetchList(query),
})

onMounted(async () => {
  await Promise.all([reload(), store.fetchSettings()])
  initialLoaded.value = true
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

const linkActions = computed(() => [
  {
    label: t('shared.cancel'),
    variant: 'ghost' as const,
    theme: 'gray' as const,
    onClick: ({ close }: { close: () => void }) => close(),
  },
  {
    label: t('goakal.actions.link'),
    variant: 'solid' as const,
    disabled: !linkInvoiceId.value,
    onClick: async () => {
      await confirmLink()
    },
  },
])

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

const secretActions = computed(() => [
  {
    label: t('shared.cancel'),
    variant: 'ghost' as const,
    theme: 'gray' as const,
    onClick: ({ close }: { close: () => void }) => close(),
  },
  {
    label: t('billing.actions.save'),
    variant: 'solid' as const,
    loading: store.settingsSaving,
    disabled: !secretValue.value.trim(),
    onClick: async () => {
      await confirmSecret()
    },
  },
])

function statusTheme(status: string): 'green' | 'blue' | 'gray' {
  if (status === 'PAID') return 'green'
  if (status === 'UNPAID') return 'blue'
  return 'gray'
}
</script>

<template>
  <AppPageHeader>
    <template #default>
      <Button
        v-if="isSuperadmin"
        variant="solid"
        theme="gray"
        icon-left="lucide-key-round"
        :label="t('goakal.actions.settings')"
        @click="secretOpen = true"
      />
    </template>
    <template #suffix>
      <Button
        v-if="isSuperadmin"
        variant="ghost"
        theme="gray"
        icon="lucide-key-round"
        :label="t('goakal.actions.settings')"
        @click="secretOpen = true"
      />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <p class="text-p-sm text-ink-gray-7">{{ t('goakal.description') }}</p>

    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('goakal.filter.search')"
    />

    <div>
      <ListState
        :loading="store.listLoading"
        :error="store.listError"
        :empty="empty"
        icon="lucide-receipt-text"
        :empty-message="search ? t('goakal.noTransactionsFound') : t('goakal.empty')"
      >
        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('goakal.columns.payer') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('goakal.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('goakal.columns.amount') }}
            </ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('goakal.columns.paidAt') }}
            </ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('goakal.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="store.items" v-slot="{ item }">
            <ListRow :value="item.id">
              <ListCell>
                <div class="flex min-w-0 flex-col">
                  <span class="truncate text-base-medium text-ink-gray-8">
                    {{ item.email || item.name || item.externalId }}
                  </span>
                  <span class="truncate text-p-sm text-ink-gray-5">
                    {{ item.externalId }}
                  </span>
                </div>
              </ListCell>
              <ListCell>
                <Badge
                  :label="item.status"
                  :theme="statusTheme(item.status)"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="text-p-sm text-ink-gray-6">
                  {{ item.amount != null ? formatRupiah(item.amount) : '—' }}
                </span>
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="text-p-sm text-ink-gray-6">
                  {{ item.paidOn ? formatDate(item.paidOn) : '—' }}
                </span>
              </ListCell>
              <ListCell>
                <Button
                  v-if="!item.invoiceId && isSuperadmin"
                  variant="ghost"
                  theme="gray"
                  icon="lucide-link"
                  :label="t('goakal.actions.link')"
                  :loading="store.linkingId === item.id"
                  @click.stop="openLink(item)"
                />
                <Badge
                  v-else-if="item.invoiceId"
                  :label="t('goakal.linked')"
                  theme="green"
                  variant="subtle"
                />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!store.listLoading && !store.listError && !empty"
        :total="store.total"
        :page="store.page"
        :per-page="perPage"
        @update:page="goToPage"
      />
    </div>

    <ErrorMessage v-if="gateReady && store.linkError" :message="store.linkError" />
  </div>

  <Dialog
    v-model:open="linkOpen"
    :title="t('goakal.link.title')"
    icon="lucide-link"
    size="md"
    :actions="linkActions"
  >
    <div class="space-y-4">
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
  </Dialog>

  <Dialog
    v-model:open="secretOpen"
    :title="t('goakal.settings.title')"
    icon="lucide-key-round"
    size="md"
    :actions="secretActions"
  >
    <div class="space-y-4">
      <p class="text-p-sm text-ink-gray-7">{{ t('goakal.settings.description') }}</p>
      <p v-if="store.settings?.configured" class="text-p-sm text-ink-gray-7">
        {{ t('goakal.settings.configured') }}
      </p>
      <TextInput
        v-model="secretValue"
        type="text"
        :label="t('goakal.settings.secret')"
        :placeholder="t('goakal.settings.secretPlaceholder')"
      />
      <ErrorMessage v-if="store.settingsSaveError" :message="store.settingsSaveError" />
    </div>
  </Dialog>
</template>
