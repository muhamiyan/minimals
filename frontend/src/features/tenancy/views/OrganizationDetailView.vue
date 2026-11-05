<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import {
  Badge,
  Button,
  ErrorMessage,
  FormControl,
  PageHeader,
  Spinner,
  Switch,
  toast,
} from 'frappe-ui'

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'
import { formatRupiah } from '@/shared/format'

import { durationLabel, usePlansStore } from '@/features/plans/store'

import MembersPanel from '../components/MembersPanel.vue'
import {
  SUB_STATUSES,
  TIER_LABELS,
  statusLabelFor,
  useTenancyStore,
  type Organization,
  type SubscriptionInput,
} from '../store'
import {
  featureLabel,
  slugify,
  validateName,
  validateSlug,
} from '../validation'

const route = useRoute()
const store = useTenancyStore()
const plans = usePlansStore()
const { t } = useI18n()

const orgId = computed(() => String(route.params.orgId ?? ''))

const statusOptions = computed(() =>
  SUB_STATUSES.map((status) => ({ label: statusLabelFor(status), value: status })),
)

const featureEntries = computed(() => Object.entries(store.features))

// --- organization form ---------------------------------------------------
const orgForm = ref({ name: '', slug: '', isActive: true })
const orgSlugTouched = ref(false)
const orgNameError = ref('')
const orgSlugError = ref('')
const savingOrg = ref(false)
let syncingOrgForm = false

watch(
  () => orgForm.value.name,
  (name) => {
    if (syncingOrgForm || orgSlugTouched.value) return
    orgForm.value.slug = slugify(name)
  },
  { flush: 'sync' },
)

function syncOrgForm(org: Organization): void {
  syncingOrgForm = true
  orgForm.value.name = org.name
  orgForm.value.slug = org.slug
  orgForm.value.isActive = org.isActive
  orgSlugTouched.value = false
  syncingOrgForm = false
}

function onOrgSlugInput(value: unknown): void {
  orgForm.value.slug = String(value ?? '')
  orgSlugTouched.value = true
}

async function saveOrg(): Promise<void> {
  if (savingOrg.value) return
  orgNameError.value = validateName(orgForm.value.name)
  orgSlugError.value = validateSlug(orgForm.value.slug)
  if (orgNameError.value || orgSlugError.value) return

  // `resolve_features` folds in organization.active, so a toggle changes it.
  const wasActive = store.current?.isActive ?? true
  savingOrg.value = true
  const saved = await store.updateOrg(orgId.value, {
    name: orgForm.value.name.trim(),
    slug: orgForm.value.slug.trim().toLowerCase(),
    isActive: orgForm.value.isActive,
  })
  savingOrg.value = false
  if (!saved) return
  syncOrgForm(saved)
  if (saved.isActive !== wasActive) store.fetchFeatures(orgId.value)
  toast.success(t('tenancy.org.updated'))
}

// --- subscription form ---------------------------------------------------
const subForm = ref({ planId: '', status: 'active', expiresOn: '' })
const planError = ref('')
const savingSub = ref(false)

const planOptions = computed(() => {
  const options = plans.options
    .filter((plan) => plan.isActive)
    .map((plan) => ({
      label: `${plan.name} · ${durationLabel(plan.durationValue, plan.durationUnit)}`,
      value: plan.id,
    }))
  // Inactive plans cannot be assigned, but the current one must stay visible
  // so the select never falls back to a blank value.
  const stored = store.current?.subscription
  if (stored?.planId && !options.some((option) => option.value === stored.planId)) {
    const known = plans.options.find((plan) => plan.id === stored.planId)
    const suffix = known && !known.isActive ? ` · ${t('plans.inactive')}` : ''
    options.unshift({
      label: `${stored.planName || stored.planId} · ${durationLabel(
        stored.planDurationValue,
        stored.planDurationUnit,
      )}${suffix}`,
      value: stored.planId,
    })
  }
  return options
})

const selectedPlan = computed(
  () => plans.options.find((plan) => plan.id === subForm.value.planId) ?? null,
)

const planMeta = computed(() => {
  const plan = selectedPlan.value
  if (!plan) return ''
  return [
    TIER_LABELS[plan.tier] ?? plan.tier,
    durationLabel(plan.durationValue, plan.durationUnit),
    plan.price == null
      ? t('tenancy.subscription.manual')
      : formatRupiah(plan.price),
  ].join(' · ')
})

function syncSubForm(org: Organization | null): void {
  const sub = org?.subscription ?? null
  subForm.value = {
    planId: sub?.planId ?? '',
    status: sub?.status ?? 'active',
    expiresOn: sub?.expiresOn ? sub.expiresOn.slice(0, 10) : '',
  }
  planError.value = ''
}

function isLapsed(iso: string): boolean {
  return iso !== '' && new Date(iso).getTime() <= Date.now()
}

// A lapsed stored date would otherwise be re-sent and keep the plan expired.
// Only the untouched stored date is dropped, never one the admin just picked.
watch(
  () => subForm.value.planId,
  () => {
    const stored = store.current?.subscription
    if (!stored?.expiresOn || !isLapsed(stored.expiresOn)) return
    const stale = stored.expiresOn.slice(0, 10)
    if (subForm.value.expiresOn === stale) subForm.value.expiresOn = ''
  },
)

async function saveSub(): Promise<void> {
  if (savingSub.value) return
  planError.value = subForm.value.planId
    ? ''
    : t('tenancy.validation.planRequired')
  if (planError.value) return

  const payload: SubscriptionInput = {
    planId: subForm.value.planId,
    status: subForm.value.status,
  }
  if (subForm.value.expiresOn) {
    payload.expiresOn = `${subForm.value.expiresOn}T00:00:00+00:00`
  }

  savingSub.value = true
  const saved = await store.saveSubscription(orgId.value, payload)
  savingSub.value = false
  if (!saved) return
  syncSubForm(store.current)
  // Plan, status, and expiry all feed `resolve_features`.
  store.fetchFeatures(orgId.value)
  toast.success(t('tenancy.subscription.updated'))
}

// --- load ----------------------------------------------------------------
async function load(): Promise<void> {
  const id = orgId.value
  if (!id) return
  store.orgSaveError = ''
  store.subSaveError = ''
  if (!plans.options.length) plans.fetchPlanOptions()
  const org = await store.fetchOrg(id)
  if (org && org.id === id) {
    syncOrgForm(org)
    syncSubForm(org)
  }
  store.fetchFeatures(id)
}

onMounted(load)
watch(orgId, (next, previous) => {
  if (next && next !== previous) load()
})
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs :title="store.current?.name" />
  </PageHeader>

  <div class="mx-auto w-full max-w-6xl px-5 py-6">
    <div v-if="store.orgLoading && !store.current" class="flex justify-center py-16">
      <Spinner />
    </div>

    <div v-else-if="store.current" class="grid gap-4 lg:grid-cols-2">
      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.org.title') }}</h2>
          <p class="text-p-sm text-ink-gray-5">{{ t('tenancy.org.description') }}</p>
        </div>
        <form class="space-y-4" @submit.prevent="saveOrg">
          <FormControl
            v-model="orgForm.name"
            :label="t('tenancy.fields.name')"
            :placeholder="t('tenancy.fields.namePlaceholder')"
            required
            :error="orgNameError"
          />
          <FormControl
            :model-value="orgForm.slug"
            :label="t('tenancy.fields.slug')"
            :description="t('tenancy.fields.slugDescription')"
            :placeholder="t('tenancy.fields.slugPlaceholder')"
            required
            :error="orgSlugError"
            @update:model-value="onOrgSlugInput"
          />
          <Switch
            v-model="orgForm.isActive"
            :label="t('tenancy.org.active')"
            :description="t('tenancy.org.activeDescription')"
          />
          <ErrorMessage v-if="store.orgSaveError" :message="store.orgSaveError" />
          <div class="flex justify-end">
            <Button
              type="submit"
              variant="solid"
              theme="gray"
              :label="t('tenancy.org.save')"
              :loading="savingOrg"
            />
          </div>
        </form>
      </section>

      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">
            {{ t('tenancy.subscription.title') }}
          </h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('tenancy.subscription.description') }}
          </p>
        </div>
        <form class="space-y-4" @submit.prevent="saveSub">
          <div class="grid gap-4 sm:grid-cols-2">
            <FormControl
              v-model="subForm.planId"
              type="select"
              :label="t('tenancy.subscription.plan')"
              :options="planOptions"
              :description="planMeta"
              :error="planError"
            />
            <FormControl
              v-model="subForm.status"
              type="select"
              :label="t('tenancy.subscription.status')"
              :options="statusOptions"
            />
          </div>
          <FormControl
            v-model="subForm.expiresOn"
            type="date"
            :label="t('tenancy.subscription.expiresOn')"
            :description="t('tenancy.subscription.expiryHelp')"
            clearable
          />
          <ErrorMessage v-if="plans.loadError" :message="plans.loadError" />
          <ErrorMessage v-if="store.subSaveError" :message="store.subSaveError" />
          <div class="flex justify-end">
            <Button
              type="submit"
              variant="solid"
              theme="gray"
              :label="t('tenancy.subscription.save')"
              :loading="savingSub"
            />
          </div>
        </form>
      </section>

      <section
        class="space-y-3 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">
            {{ t('tenancy.org.featuresTitle') }}
          </h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('tenancy.org.featuresDescription') }}
          </p>
        </div>
        <div v-if="store.featuresLoading" class="flex justify-center py-6">
          <Spinner />
        </div>
        <ErrorMessage v-else-if="store.featuresError" :message="store.featuresError" />
        <div v-else-if="featureEntries.length" class="flex flex-wrap gap-2">
          <Badge
            v-for="[flag, enabled] in featureEntries"
            :key="flag"
            :label="featureLabel(flag)"
            :theme="enabled ? 'green' : 'gray'"
            variant="subtle"
          />
        </div>
        <p v-else class="text-p-sm text-ink-gray-5">
          {{ t('tenancy.org.featuresEmpty') }}
        </p>
      </section>

      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <MembersPanel :org-id="orgId" :can-manage="true" />
      </section>
    </div>

    <div
      v-else
      class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 px-5 py-8"
    >
      <ErrorMessage :message="store.orgError || t('tenancy.org.notFound')" />
      <Button
        class="mt-4"
        :label="t('tenancy.org.back')"
        variant="outline"
        icon-left="lucide-arrow-left"
        :route="{ name: 'Tenancy' }"
      />
    </div>
  </div>
</template>
