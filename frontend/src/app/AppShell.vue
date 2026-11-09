<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Avatar,
  DesktopShell,
  MobileNavItem,
  MobileShell,
  SidebarHeader,
} from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { useBillingStore } from '@/features/billing/store'
import { usePlansStore } from '@/features/plans/store'
import { useTenancyStore } from '@/features/tenancy/store'
import { useTodosStore } from '@/features/todos/store'
import ForbiddenDialog from '@/shared/components/ForbiddenDialog.vue'
import BrandLogo from '@/shared/components/BrandLogo.vue'
import MobileBottomNav from '@/shared/shell/MobileBottomNav.vue'
import MobileMenuSheet from '@/shared/shell/MobileMenuSheet.vue'
import ShellSidebar from '@/shared/shell/ShellSidebar.vue'
import type { ShellNavItem } from '@/shared/shell/types'
import { useMediaQuery } from '@/shared/composables/useMediaQuery'
import { brand } from '@/shared/brand'
import { useMenuStore } from './menuStore'
import { mobileNavItems } from './navigation'
import ThemeSwitcher from './ThemeSwitcher.vue'
import UserSettingsDialog from './UserSettingsDialog.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const menu = useMenuStore()
const tenancy = useTenancyStore()
const billing = useBillingStore()
const plans = usePlansStore()
const todos = useTodosStore()
const { t } = useI18n()

watch(
  () => auth.user?.id,
  (userId) => {
    if (userId) menu.fetchPreference()
    else menu.reset()
  },
  { immediate: true },
)

// AppShell only wraps authenticated routes, so this is safe to fire once here.
// The router guard may have already loaded myOrgs (onboarding gate) — don't
// ask a second time, but features always depend on the settled org list.
onMounted(async () => {
  if (!tenancy.myOrgsLoaded) await tenancy.fetchMyOrgs()
  tenancy.fetchDomainModes()
  await tenancy.fetchActiveFeatures()
})

const isFullscreen = computed(
  () => route.meta.fullscreen === true || route.query.fullscreen === '1',
)

const isDesktop = useMediaQuery('(min-width: 640px)')

const displayName = computed(() => auth.user?.fullName || auth.user?.email || '')

const sidebarCollapsed = ref(false)
const settingsOpen = ref(false)
const settingsTab = ref('profile')

function openSettings(tab: 'profile' | 'preferences' = 'profile') {
  settingsTab.value = tab
  settingsOpen.value = true
}

function orgRoleLabel(role: string | null | undefined): string {
  if (role === 'owner') return t('orgSwitcher.owner')
  if (role === 'member') return t('orgSwitcher.member')
  return ''
}

async function switchOrg(orgId: string): Promise<void> {
  if (orgId === tenancy.currentOrg?.id) return
  if (!tenancy.setActiveOrg(orgId)) return
  tenancy.fetchActiveFeatures()
  if (route.name === 'MyOrganization') {
    await router.push({ name: 'MyOrganization', params: { orgId } })
  }
}

async function onSwitchOrg(orgId: string): Promise<void> {
  settingsOpen.value = false
  await switchOrg(orgId)
}

const headerMenu = computed(() => {
  const orgs = tenancy.myOrgs.map((org) => ({
    label: org.name,
    description: orgRoleLabel(org.myRole),
    selected: org.id === tenancy.currentOrg?.id,
    onClick: () => switchOrg(org.id),
  }))
  return [
    {
      group: t('menu.theme'),
      options: [
        {
          label: t('menu.theme'),
          slots: { label: () => h(ThemeSwitcher) },
        },
      ],
    },
    ...(orgs.length ? [{ group: t('orgSwitcher.title'), options: orgs }] : []),
    {
      label: t('menu.settings'),
      icon: 'lucide-settings',
      onClick: () => openSettings(),
    },
    { label: t('menu.logout'), icon: 'lucide-log-out', onClick: onLogout },
  ]
})

// The shell components take resolved rows: labels are translated here and the
// active state follows the route name (nav keys mirror route names).
const menuItems = computed<ShellNavItem[]>(() =>
  menu.items.map((item) => ({
    key: item.key,
    label: t(item.labelKey),
    icon: item.icon,
    route: item.route,
    active: String(route.name) === item.key,
  })),
)
const tabItems = computed<ShellNavItem[]>(() =>
  mobileNavItems(menu.items).map((item) => ({
    key: item.key,
    label: t(item.mobileLabelKey ?? item.labelKey),
    icon: item.icon,
    route: item.route,
    active: String(route.name) === item.key,
  })),
)

async function onLogout() {
  await auth.logout()
  tenancy.resetMyOrgs()
  billing.reset()
  plans.reset()
  todos.reset()
  await router.replace('/login')
}
</script>

<template>
  <router-view v-if="isFullscreen" />

  <DesktopShell v-else-if="isDesktop" :scroll="route.meta.scroll !== false">
    <template #sidebar>
      <ShellSidebar
        v-model:collapsed="sidebarCollapsed"
        :items="menuItems"
        :section-label="t('menu.section')"
      >
        <template #header>
          <SidebarHeader
            :title="brand.name"
            :subtitle="displayName"
            :menu-items="headerMenu"
          >
            <template #prefix>
              <BrandLogo size="fill" :alt="brand.name">
                <div
                  class="flex h-full w-full items-center justify-center bg-surface-gray-4 text-ink-gray-7"
                >
                  {{ brand.name.charAt(0).toUpperCase() }}
                </div>
              </BrandLogo>
            </template>
          </SidebarHeader>
        </template>
      </ShellSidebar>
    </template>

    <router-view />
  </DesktopShell>

  <MobileShell v-else>
    <router-view />

    <template #nav>
      <MobileBottomNav :items="tabItems">
        <MobileNavItem
          :label="t('settings.profile.title')"
          :active="settingsOpen"
          @click="openSettings('profile')"
        >
          <template #default="{ active }">
            <Avatar
              :label="displayName"
              size="md"
              shape="circle"
              :class="active ? 'ring-2 ring-outline-gray-4' : ''"
            />
          </template>
        </MobileNavItem>
      </MobileBottomNav>
    </template>
  </MobileShell>

  <MobileMenuSheet :items="menuItems" :title="t('menu.menu')" @logout="onLogout" />

  <UserSettingsDialog
    v-model:open="settingsOpen"
    v-model:tab="settingsTab"
    :show-organizations="!isDesktop"
    @switch-org="onSwitchOrg"
    @logout="onLogout"
  />
  <ForbiddenDialog />
</template>
