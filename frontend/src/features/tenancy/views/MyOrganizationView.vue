<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { Badge, Button, ErrorMessage, PageHeader, Spinner } from 'frappe-ui'
import type { ListColumnsByBreakpoint } from 'frappe-ui/list'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import ListHead from '@/shared/components/ListHead.vue'
import ListRowOpenButton from '@/shared/components/ListRowOpenButton.vue'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import { formatDate, formatRupiah } from '@/shared/format'
import { LIST_ROW_SURFACE_CLASS } from '@/shared/listRow'
import InvoicePrintDialog from '@/features/billing/components/InvoicePrintDialog.vue'
import {
  invoiceStatusLabel,
  invoiceStatusTheme,
  type Invoice,
  useBillingStore,
} from '@/features/billing/store'

import InviteCodesPanel from '../components/InviteCodesPanel.vue'
import MembersPanel from '../components/MembersPanel.vue'
import {
  roleLabel,
  statusLabel,
  statusTheme,
  tierLabel,
  tierTheme,
  useTenancyStore,
  type Organization,
} from '../store'

// base: Invoice, Amount, Actions — md: + Period, Status
const invoiceColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '120px', '120px'],
  md: ['minmax(0,1fr)', '130px', '120px', '100px', '120px'],
}

const route = useRoute()
const store = useTenancyStore()
const billing = useBillingStore()
const { t } = useI18n()

const orgId = computed(() => String(route.params.orgId ?? ''))

/**
 * `myRole` only ships on `/my-organizations`, never on the single-org
 * endpoint, so ownership is resolved from that list.
 */
const org = computed<Organization | null>(
  () => store.myOrgs.find((item) => item.id === orgId.value) ?? null,
)

const isOwner = computed(() => org.value?.myRole === 'owner')

const printInvoice = ref<Invoice | null>(null)
const printOpen = ref(false)

function openPrint(invoice: Invoice): void {
  printInvoice.value = invoice
  printOpen.value = true
}

watch(
  () => org.value?.id,
  (id) => {
    if (!id) return
    store.setActiveOrg(id)
    store.fetchActiveFeatures()
  },
  { immediate: true },
)

onMounted(() => {
  // A deep link arrives before the list has loaded.
  if (!store.myOrgs.length) store.fetchMyOrgs()
})

// The owner's invoice card — resolves once myOrgs has settled (deep links).
watch(
  () => (isOwner.value ? orgId.value : ''),
  (id) => {
    if (id) billing.fetchOrgInvoices(id)
    else billing.clearOrgInvoices()
  },
  { immediate: true },
)
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs :title="org?.name" />
  </PageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div v-if="store.myOrgsLoading && !org" class="flex justify-center py-10">
      <Spinner />
    </div>

    <template v-else-if="org">
      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.org.title') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('tenancy.org.ownerDescription') }}
          </p>
        </div>
        <dl class="grid gap-4 sm:grid-cols-2">
          <div class="space-y-1">
            <dt class="text-p-xs text-ink-gray-5">{{ t('tenancy.fields.name') }}</dt>
            <dd class="text-base-medium text-ink-gray-8">{{ org.name }}</dd>
          </div>
          <div class="space-y-1">
            <dt class="text-p-xs text-ink-gray-5">{{ t('tenancy.fields.slug') }}</dt>
            <dd class="text-base-medium text-ink-gray-8">{{ org.slug }}</dd>
          </div>
          <div class="space-y-1">
            <dt class="text-p-xs text-ink-gray-5">
              {{ t('tenancy.subscription.title') }}
            </dt>
            <dd class="flex flex-wrap gap-2">
              <Badge
                :label="tierLabel(org.subscription)"
                :theme="tierTheme(org.subscription)"
                variant="subtle"
              />
              <Badge
                :label="statusLabel(org.subscription)"
                :theme="statusTheme(org.subscription)"
                variant="subtle"
              />
            </dd>
          </div>
          <div class="space-y-1">
            <dt class="text-p-xs text-ink-gray-5">{{ t('tenancy.org.yourRole') }}</dt>
            <dd>
              <Badge
                :label="roleLabel(org.myRole ?? 'member')"
                :theme="isOwner ? 'violet' : 'gray'"
                variant="subtle"
              />
            </dd>
          </div>
        </dl>
      </section>

      <section
        v-if="isOwner"
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">{{ t('billing.org.title') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('billing.org.description') }}
          </p>
        </div>

        <div>
          <div v-if="billing.orgInvoicesLoading" class="flex justify-center py-10">
            <Spinner />
          </div>
          <ErrorMessage
            v-else-if="billing.orgInvoicesError"
            :message="billing.orgInvoicesError"
          />

          <div
            v-else-if="!billing.orgInvoices.length"
            class="flex flex-col items-center gap-2 py-10 text-center"
          >
            <span class="lucide-receipt-text size-8 text-ink-gray-4" aria-hidden="true" />
            <p class="text-p-sm text-ink-gray-5">{{ t('billing.org.none') }}</p>
          </div>

          <List v-else class="list-row-px-3" :columns="invoiceColumns">
            <ListHead>
              <ListHeaderCell>{{ t('billing.columns.invoice') }}</ListHeaderCell>
              <ListHeaderCell class="hidden md:flex">
                {{ t('billing.columns.period') }}
              </ListHeaderCell>
              <ListHeaderCell>{{ t('billing.columns.amount') }}</ListHeaderCell>
              <ListHeaderCell class="hidden md:flex">
                {{ t('billing.columns.status') }}
              </ListHeaderCell>
              <ListHeaderCell class="justify-end">
                <span class="sr-only">{{ t('billing.columns.actions') }}</span>
              </ListHeaderCell>
            </ListHead>
            <ListRows :items="billing.orgInvoices" row-key="id" v-slot="{ item }">
              <ListRow :class="LIST_ROW_SURFACE_CLASS">
                <ListCell class="min-w-0">
                  <ListRowOpenButton
                    :label="`${t('billing.actions.print')}: ${item.number}`"
                    @click="openPrint(item)"
                  />
                  <div class="min-w-0">
                    <div class="truncate text-base-medium text-ink-gray-8">
                      {{ item.number }}
                    </div>
                    <div class="truncate text-p-xs text-ink-gray-5">
                      {{ t('billing.org.due', { date: formatDate(item.dueOn) }) }}
                    </div>
                  </div>
                </ListCell>
                <ListCell class="hidden md:flex">
                  <span class="text-p-sm text-ink-gray-6">
                    {{ formatDate(item.periodStart) }}
                  </span>
                </ListCell>
                <ListCell>
                  <span class="text-base-medium text-ink-gray-8">
                    {{ formatRupiah(item.amount) }}
                  </span>
                </ListCell>
                <ListCell class="hidden md:flex">
                  <Badge
                    :label="invoiceStatusLabel(item.status)"
                    :theme="invoiceStatusTheme(item.status)"
                    variant="subtle"
                  />
                </ListCell>
                <ListCell class="justify-end">
                  <Button
                    icon="lucide-printer"
                    :label="t('billing.actions.print')"
                    variant="ghost"
                    class="relative"
                    @click="openPrint(item)"
                  />
                </ListCell>
              </ListRow>
            </ListRows>
          </List>
        </div>
      </section>

      <section
        v-if="isOwner"
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <InviteCodesPanel :org-id="org.id" />
      </section>

      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <MembersPanel :org-id="org.id" :can-manage="isOwner" />

        <p v-if="!isOwner" class="text-p-sm text-ink-gray-5">
          {{ t('tenancy.org.onlyOwners') }}
        </p>
      </section>
    </template>

    <div v-else class="space-y-4">
      <ErrorMessage
        :message="store.myOrgsError || t('tenancy.org.notFound')"
      />
      <Button
        :label="t('tenancy.org.back')"
        variant="outline"
        icon-left="lucide-arrow-left"
        :route="{ name: 'MyOrganizations' }"
      />
    </div>

    <InvoicePrintDialog v-model:open="printOpen" :invoice="printInvoice" />
  </div>
</template>
