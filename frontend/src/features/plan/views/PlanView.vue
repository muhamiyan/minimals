<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  PageHeader,
  Spinner,
  toast,
} from 'frappe-ui'

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import { formatRupiah } from '@/shared/format'

import { TIER_LABELS, useTenancyStore } from '@/features/tenancy/store'
import { featureLabel } from '@/features/tenancy/validation'
import { durationLabel, type Plan } from '@/features/plans/store'
import { usePlanStore } from '../store'

const { t } = useI18n()
const tenancy = useTenancyStore()
const store = usePlanStore()
const router = useRouter()

const domainMode = computed(() => tenancy.domainMode('plans'))
const isMaintenance = computed(() => domainMode.value === 'maintenance')
const isDev = computed(() => domainMode.value === 'dev')

// Same gate as the plans console: never render the catalog before the
// caller's orgs and the domain mode are both settled.
const gateReady = computed(() => tenancy.myOrgsLoaded || tenancy.domainMode('plans') !== '')

const currentOrg = computed(() => tenancy.currentOrg)
const currentPlanId = computed(() => currentOrg.value?.subscription?.planId ?? null)

const featureKeys = computed(() => [
  ...new Set(store.items.flatMap((plan) => Object.keys(plan.features ?? {}))),
])

const pendingPlan = computed(() =>
  store.pendingInvoice?.planId
    ? (store.items.find((plan) => plan.id === store.pendingInvoice?.planId) ?? null)
    : null,
)

onMounted(() => {
  store.fetchCatalog()
})

watch(
  () => currentOrg.value?.id,
  (orgId) => {
    if (orgId) store.fetchPending(orgId)
  },
  { immediate: true },
)

const TIER_ACCENTS: Record<string, { chip: string; icon: string }> = {
  community: {
    chip: 'from-surface-green-2 to-surface-elevation-2 text-ink-green-8',
    icon: 'lucide-leaf',
  },
  professional: {
    chip: 'from-surface-violet-2 to-surface-elevation-2 text-ink-violet-7',
    icon: 'lucide-rocket',
  },
}
const DEFAULT_ACCENT = {
  chip: 'from-surface-gray-2 to-surface-elevation-2 text-ink-gray-7',
  icon: 'lucide-package',
}

function accentFor(tier: string): { chip: string; icon: string } {
  return TIER_ACCENTS[tier] ?? DEFAULT_ACCENT
}

function isCurrent(plan: Plan): boolean {
  return currentPlanId.value !== null && plan.id === currentPlanId.value
}

function canSelect(plan: Plan): boolean {
  // No active org → no org to switch, so nothing is selectable (the
  // menu gate already handles most of this; this is belt and braces).
  // An unpaid switch invoice blocks a second request until it is
  // paid or voided.
  return (
    plan.isActive &&
    !isCurrent(plan) &&
    !isMaintenance.value &&
    currentOrg.value !== null &&
    !store.pendingInvoice
  )
}

function planPrice(plan: Plan): string | null {
  return plan.price == null ? null : formatRupiah(plan.price)
}

const confirmTarget = ref<Plan | null>(null)
const confirmOpen = ref(false)

function openConfirm(plan: Plan): void {
  if (!canSelect(plan)) return
  store.actionError = ''
  confirmTarget.value = plan
  confirmOpen.value = true
}

async function confirmSwitch(): Promise<void> {
  const target = confirmTarget.value
  const orgId = currentOrg.value?.id
  if (!target || !orgId || store.switchingId) return
  const invoice = await store.switchPlan(orgId, target.id)
  if (!invoice) return
  confirmOpen.value = false
  toast.success(t('plan.switchRequested', { number: invoice.number }))
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
  </PageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <p v-if="isMaintenance" class="text-p-sm text-ink-gray-5">
      {{ t('plans.maintenanceHint') }}
    </p>

    <div
      v-if="store.pendingInvoice"
      class="flex flex-wrap items-center justify-between gap-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 px-4 py-3"
    >
      <div class="flex min-w-0 items-center gap-3">
        <span class="lucide-clock size-5 shrink-0 text-ink-gray-5" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-7">
          {{
            pendingPlan
              ? t('plan.pendingSwitch', { name: pendingPlan.name, number: store.pendingInvoice.number })
              : t('plan.pendingSwitchGeneric', { number: store.pendingInvoice.number })
          }}
        </p>
      </div>
      <Button
        :label="t('plan.viewBilling')"
        variant="outline"
        @click="router.push({ name: 'Billing' })"
      />
    </div>

    <ErrorMessage v-if="store.loadError" :message="store.loadError" />

    <div v-if="store.loading" class="flex justify-center py-10">
      <Spinner />
    </div>

    <div v-else-if="store.loadError" class="flex justify-center py-8">
      <Button
        :label="t('plans.retry')"
        variant="outline"
        icon-left="lucide-refresh-cw"
        @click="store.fetchCatalog()"
      />
    </div>

    <div
      v-else-if="!store.items.length"
      class="flex flex-col items-center gap-2 py-10 text-center"
    >
      <span class="lucide-package size-8 text-ink-gray-4" aria-hidden="true" />
      <p class="text-p-sm text-ink-gray-5">{{ t('plan.empty') }}</p>
    </div>

    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <div
        v-for="plan in store.items"
        :key="plan.id"
        class="flex h-full flex-col gap-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 transition-colors"
        :class="isCurrent(plan) ? 'border-outline-violet-3 bg-surface-violet-1' : ''"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex min-w-0 items-center gap-3">
            <span
              class="flex size-11 shrink-0 items-center justify-center rounded-6 bg-gradient-to-br"
              :class="accentFor(plan.tier).chip"
            >
              <span :class="['size-6', accentFor(plan.tier).icon]" aria-hidden="true" />
            </span>
            <div class="min-w-0">
              <div class="truncate text-base-medium text-ink-gray-8">
                {{ plan.name }}
              </div>
              <div class="mt-0.5 text-p-xs text-ink-gray-5">
                {{ TIER_LABELS[plan.tier] ?? plan.tier }}
              </div>
            </div>
          </div>
          <div class="flex shrink-0 flex-wrap justify-end gap-1">
            <Badge
              v-if="isCurrent(plan)"
              :label="t('plan.currentPlan')"
              theme="violet"
              variant="subtle"
            />
            <Badge
              v-if="!plan.isActive"
              :label="t('plan.unavailable')"
              theme="gray"
              variant="subtle"
            />
          </div>
        </div>

        <div>
          <div class="text-2xl-semibold leading-tighter text-ink-gray-9">
            {{ planPrice(plan) ?? t('plans.manual') }}
          </div>
          <div class="mt-0.5 text-p-xs text-ink-gray-5">
            {{ durationLabel(plan.durationValue, plan.durationUnit) }}
          </div>
        </div>

        <ul v-if="featureKeys.length" class="space-y-1.5 border-t border-outline-gray-1 pt-4">
          <li
            v-for="key in featureKeys"
            :key="key"
            class="flex items-center gap-2"
          >
            <span
              v-if="plan.features[key]"
              class="lucide-check size-4 text-ink-gray-8"
              aria-hidden="true"
            />
            <span
              v-else
              class="lucide-minus size-4 text-ink-gray-4"
              aria-hidden="true"
            />
            <span
              class="text-p-sm"
              :class="plan.features[key] ? 'text-ink-gray-8' : 'text-ink-gray-5'"
            >
              {{ featureLabel(key) }}
            </span>
          </li>
        </ul>

        <div class="mt-auto border-t border-outline-gray-1 pt-4">
          <Button
            class="w-full justify-center"
            :variant="isCurrent(plan) || !plan.isActive ? 'subtle' : 'solid'"
            theme="gray"
            size="md"
            :label="
              isCurrent(plan)
                ? t('plan.currentPlan')
                : !plan.isActive
                  ? t('plan.unavailable')
                  : t('plan.select')
            "
            :icon-left="isCurrent(plan) ? 'lucide-check' : undefined"
            :icon-right="isCurrent(plan) || !plan.isActive ? undefined : 'lucide-arrow-right'"
            :disabled="!canSelect(plan)"
            :loading="store.switchingId === plan.id"
            @click="openConfirm(plan)"
          />
        </div>
      </div>
    </div>
  </div>

  <Dialog
    v-model:open="confirmOpen"
    :title="confirmTarget ? t('plan.confirmTitle', { name: confirmTarget.name }) : ''"
    icon="lucide-package"
    size="sm"
  >
    <div class="space-y-4">
      <p v-if="confirmTarget" class="text-p-sm text-ink-gray-6">
        {{
          t('plan.confirmBody', {
            name: confirmTarget.name,
            price: planPrice(confirmTarget) ?? '',
          })
        }}
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
          :label="t('plan.confirm')"
          variant="solid"
          theme="gray"
          :loading="Boolean(store.switchingId)"
          @click="confirmSwitch"
        />
      </div>
    </template>
  </Dialog>
</template>
