<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Spinner } from 'frappe-ui'

import PanelCard from '@/shared/components/PanelCard.vue'
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

const user = computed(() => auth.user)
const org = computed(() => tenancy.currentOrg)
const advancedReporting = computed(() => tenancy.hasFeature('advanced_reporting'))
</script>

<template>
  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <PanelCard class="space-y-1">
      <p class="text-p-sm text-ink-gray-5">{{ t('dash.welcomeBack') }}</p>
      <div class="text-xl-semibold text-ink-gray-8">
        {{ user?.fullName || user?.username }}
      </div>
      <p class="text-p-sm text-ink-gray-5">{{ user?.email }}</p>
    </PanelCard>

    <PanelCard :title="t('dash.roles')">
      <div class="mt-3 flex flex-wrap gap-2">
        <Badge v-if="user?.appRole" :label="user.appRole" theme="blue" />
        <Badge v-for="role in user?.roles ?? []" :key="role" :label="role" />
        <p
          v-if="!user?.appRole && !user?.roles?.length"
          class="text-p-sm text-ink-gray-5"
        >
          {{ t('dash.noRoles') }}
        </p>
      </div>
    </PanelCard>

    <PanelCard :title="t('dash.currentOrg')">
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
    </PanelCard>

    <PanelCard :title="t('dash.advancedReporting')">
      <p v-if="advancedReporting" class="mt-3 text-p-sm text-ink-gray-5">
        {{ t('dash.reportingEnabled') }}
      </p>
      <p v-else-if="tenancy.activeFeaturesLoading" class="mt-3 text-p-sm text-ink-gray-4">
        {{ t('dash.checkingPlan') }}
      </p>
      <p v-else class="mt-3 text-p-sm text-ink-gray-5">
        {{ t('dash.reportingUpsell') }}
      </p>
    </PanelCard>
  </div>
</template>
