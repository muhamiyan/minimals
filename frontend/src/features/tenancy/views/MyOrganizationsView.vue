<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Badge, Button, ErrorMessage, Spinner, toast } from 'frappe-ui'
import type { ListColumnsByBreakpoint } from 'frappe-ui/list'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListRowOpenButton from '@/shared/components/ListRowOpenButton.vue'
import { LIST_ROW_SURFACE_CLASS } from '@/shared/listRow'

import {
  statusLabel,
  statusTheme,
  tierLabel,
  tierTheme,
  useTenancyStore,
  type Organization,
} from '../store'

// base: Organization, Default, Open — md: + Tier, Status
const orgColumns: ListColumnsByBreakpoint = {
  base: ['minmax(0,1fr)', '120px', '36px'],
  md: ['minmax(0,1fr)', '120px', '110px', '120px', '36px'],
}

const store = useTenancyStore()
const router = useRouter()
const { t } = useI18n()
const switchingId = ref<string | null>(null)

function isCurrent(org: Organization): boolean {
  return store.currentOrg?.id === org.id
}

function isDefault(org: Organization): boolean {
  return store.defaultOrgId === org.id
}

function openOrg(org: Organization): void {
  store.setActiveOrg(org.id)
  store.fetchActiveFeatures()
  router.push({ name: 'MyOrganization', params: { orgId: org.id } })
}

async function makeDefault(orgId: string): Promise<void> {
  if (switchingId.value) return
  switchingId.value = orgId
  const switched = await store.setDefaultOrg(orgId)
  switchingId.value = null
  if (!switched) return
  toast.success(t('tenancy.myOrgs.defaultUpdated'))
}

onMounted(() => {
  store.fetchMyOrgs().then(() => store.fetchActiveFeatures())
})
</script>

<template>
  <AppPageHeader />

  <div class="mx-auto w-full max-w-6xl space-y-3 px-5 py-6">
    <ErrorMessage v-if="store.myOrgsError" :message="store.myOrgsError" />

    <div>
      <div v-if="store.myOrgsLoading" class="flex justify-center py-10">
        <Spinner />
      </div>

      <div
        v-else-if="!store.myOrgs.length"
        class="flex flex-col items-center gap-2 py-10 text-center"
      >
        <span class="lucide-building-2 size-8 text-ink-gray-4" aria-hidden="true" />
        <p class="text-p-sm text-ink-gray-5">
          {{ t('tenancy.myOrgs.emptyOnboarding') }}
        </p>
      </div>

      <List v-else class="list-row-px-3" :columns="orgColumns">
        <ListHead>
          <ListHeaderCell>{{ t('tenancy.myOrgs.organization') }}</ListHeaderCell>
          <ListHeaderCell class="hidden md:flex">{{ t('tenancy.myOrgs.tier') }}</ListHeaderCell>
          <ListHeaderCell class="hidden md:flex">{{ t('tenancy.myOrgs.status') }}</ListHeaderCell>
          <ListHeaderCell class="justify-end">{{ t('tenancy.myOrgs.default') }}</ListHeaderCell>
          <ListHeaderCell class="justify-end">
            <span class="sr-only">{{ t('tenancy.myOrgs.open') }}</span>
          </ListHeaderCell>
        </ListHead>
        <ListRows :items="store.myOrgs" row-key="id" v-slot="{ item }">
          <ListRow :class="LIST_ROW_SURFACE_CLASS">
            <ListCell class="min-w-0">
              <ListRowOpenButton
                :label="`${t('tenancy.myOrgs.open')}: ${item.name}`"
                @click="openOrg(item)"
              />
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <div class="min-w-0 flex-1 truncate text-base-medium text-ink-gray-8">
                    {{ item.name }}
                  </div>
                  <Badge
                    v-if="isCurrent(item)"
                    :label="t('tenancy.myOrgs.current')"
                    theme="green"
                    variant="subtle"
                    class="shrink-0"
                  />
                </div>
                <div class="truncate text-p-xs text-ink-gray-5">{{ item.slug }}</div>
              </div>
            </ListCell>
            <ListCell class="hidden md:flex">
              <Badge
                :label="tierLabel(item.subscription)"
                :theme="tierTheme(item.subscription)"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="hidden md:flex">
              <Badge
                :label="statusLabel(item.subscription)"
                :theme="statusTheme(item.subscription)"
                variant="subtle"
              />
            </ListCell>
            <ListCell class="justify-end">
              <Badge
                v-if="isDefault(item)"
                :label="t('tenancy.myOrgs.default')"
                theme="blue"
                variant="subtle"
              />
              <Button
                v-else
                :label="t('tenancy.myOrgs.makeDefault')"
                variant="outline"
                class="relative"
                :loading="switchingId === item.id"
                @click="makeDefault(item.id)"
              />
            </ListCell>
            <ListCell class="justify-end">
              <Button
                icon="lucide-chevron-right"
                :label="t('tenancy.myOrgs.open')"
                variant="ghost"
                class="relative"
                @click="openOrg(item)"
              />
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
    </div>
  </div>
</template>
