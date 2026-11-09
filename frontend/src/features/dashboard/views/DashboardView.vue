<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, PageHeader, Spinner } from 'frappe-ui'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'

import { useAuthStore } from '@/features/auth/store'
import {
  statusLabel,
  statusTheme,
  tierLabel,
  tierTheme,
  useTenancyStore,
} from '@/features/tenancy/store'

const auth = useAuthStore()
const tenancy = useTenancyStore()
const { t } = useI18n()

const org = computed(() => tenancy.currentOrg)
const advancedReporting = computed(() => tenancy.hasFeature('advanced_reporting'))

const gateReady = computed(() => auth.checked)

onMounted(() => {
  if (!auth.checked) auth.fetchMe()
  if (!tenancy.myOrgs.length) tenancy.fetchMyOrgs()
  tenancy.fetchActiveFeatures()
})
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
  </PageHeader>

  <Spinner v-if="!gateReady" />

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <p class="text-p-sm text-ink-gray-5">{{ t('dash.welcomeBack') }}</p>
      <div class="text-xl-semibold text-ink-gray-8">
        {{ auth.user?.fullName || auth.user?.username }}
      </div>
      <p class="text-p-sm text-ink-gray-5">{{ auth.user?.email }}</p>
    </div>

    <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <div class="text-base-medium text-ink-gray-8">{{ t('dash.roles') }}</div>
      <div class="mt-3 flex flex-wrap gap-2">
        <Badge v-if="auth.user?.appRole" :label="auth.user.appRole" />
        <Badge v-for="role in auth.user?.roles ?? []" :key="role" :label="role" />
        <p
          v-if="!auth.user?.appRole && !auth.user?.roles?.length"
          class="text-p-sm text-ink-gray-5"
        >
          {{ t('dash.noRoles') }}
        </p>
      </div>
    </div>

    <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <div class="text-base-medium text-ink-gray-8">{{ t('dash.currentOrg') }}</div>
      <div v-if="tenancy.myOrgsLoading && !org" class="mt-3 flex justify-center py-4">
        <Spinner />
      </div>
      <template v-else-if="org">
        <div class="mt-3 flex flex-wrap items-center gap-2">
          <span class="text-p-base text-ink-gray-8">{{ org.name }}</span>
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
        </div>
        <p class="mt-2 text-p-sm text-ink-gray-5">{{ t('dash.orgFeaturesNote') }}</p>
      </template>
      <p v-else class="mt-3 text-p-sm text-ink-gray-5">
        {{
          tenancy.myOrgsLoaded
            ? t('dash.noOrgEmpty')
            : t('dash.noOrgFeature')
        }}
      </p>
    </div>

    <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <div class="text-base-medium text-ink-gray-8">
        {{ t('dash.advancedReporting') }}
      </div>
      <p v-if="advancedReporting" class="mt-3 text-p-sm text-ink-gray-5">
        {{ t('dash.reportingEnabled') }}
      </p>
      <p v-else-if="tenancy.activeFeaturesLoading" class="mt-3 text-p-sm text-ink-gray-4">
        {{ t('dash.checkingPlan') }}
      </p>
      <p v-else class="mt-3 text-p-sm text-ink-gray-5">
        {{ t('dash.reportingUpsell') }}
      </p>
    </div>
  </div>
</template>
