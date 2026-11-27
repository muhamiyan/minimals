<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Avatar,
  DesktopShell,
  MobileNavItem,
  MobileShell,
  Sidebar,
  SidebarCollapseToggle,
  SidebarHeader,
  SidebarItem,
  SidebarSection,
} from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import ForbiddenDialog from '@/shared/components/ForbiddenDialog.vue'
import BrandLogo from '@/shared/components/BrandLogo.vue'
import SidebarNavGroup from '@/shared/components/SidebarNavGroup.vue'
import MobileBottomNav from '@/shared/shell/MobileBottomNav.vue'
import MobileMenuSheet from '@/shared/shell/MobileMenuSheet.vue'
import type { ShellNavItem } from '@/shared/shell/types'
import { useMediaQuery } from '@/shared/composables/useMediaQuery'
import { brand } from '@/shared/brand'
import { useMenuStore } from './menuStore'
import {
  findActiveGroupKey,
  flattenLeaves,
  isNavGroup,
  matchesPath,
  type NavGroup,
  type NavLeaf,
} from './navigation'
import ThemeSwitcher from './ThemeSwitcher.vue'
import UserSettingsDialog from './UserSettingsDialog.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const menu = useMenuStore()
const { t } = useI18n()

watch(
  () => auth.user?.id,
  (userId) => {
    if (userId) menu.fetchPreference()
    else menu.reset()
  },
  { immediate: true },
)

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

const headerMenu = computed(() => [
  {
    group: t('menu.theme'),
    options: [
      {
        label: t('menu.theme'),
        slots: { label: () => h(ThemeSwitcher) },
      },
    ],
  },
  {
    label: t('menu.settings'),
    icon: 'lucide-settings',
    onClick: () => openSettings(),
  },
  { label: t('menu.logout'), icon: 'lucide-log-out', onClick: onLogout },
])

const isAdmin = computed(() => auth.user?.appRole === 'admin')

function inScope(node: { requireAdmin?: boolean }): boolean {
  return !node.requireAdmin || isAdmin.value
}

const scopedRoots = computed(() => menu.roots.filter(inScope))
const rootLeaves = computed(() =>
  scopedRoots.value.filter((root): root is NavLeaf => !isNavGroup(root)),
)
const navGroups = computed(() => scopedRoots.value.filter(isNavGroup))
const mobileItems = computed(() =>
  flattenLeaves(scopedRoots.value, menu.hidden, inScope),
)

const path = computed(() => route.path)
const leafActive = (leaf: NavLeaf) => matchesPath(leaf, path.value)

const menuItems = computed<ShellNavItem[]>(() =>
  mobileItems.value.map((item) => ({
    key: item.key,
    label: t(item.labelKey),
    icon: item.icon,
    route: item.route,
    active: leafActive(item),
  })),
)

const tabItems = computed<ShellNavItem[]>(() =>
  menuItems.value.slice(0, 3).map((item, index) => ({
    ...item,
    label: t(
      mobileItems.value[index].mobileLabelKey ?? mobileItems.value[index].labelKey,
    ),
  })),
)

function groupChildren(group: NavGroup): NavLeaf[] {
  return group.children.filter(
    (child) => inScope(child) && !menu.hidden.includes(child.key),
  )
}

const activeGroupKey = computed(() =>
  findActiveGroupKey(navGroups.value, path.value),
)

type SidebarGroupInstance = InstanceType<typeof SidebarNavGroup>
const groupRefs = ref<Record<string, SidebarGroupInstance | null>>({})

function setGroupRef(key: string, el: unknown) {
  groupRefs.value[key] = (el as SidebarGroupInstance | null) ?? null
}

watch(activeGroupKey, (key) => {
  if (key) groupRefs.value[key]?.expand()
})

async function onLogout() {
  await auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <router-view v-if="isFullscreen" />

  <DesktopShell v-else-if="isDesktop" :scroll="route.meta.scroll !== false">
    <template #sidebar>
      <Sidebar v-model:collapsed="sidebarCollapsed" class="border-r">
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

        <div class="flex-1 overflow-y-auto space-y-0.5 px-2 pb-2">
          <SidebarSection v-if="rootLeaves.length" :label="t('menu.section')">
            <SidebarItem
              v-for="item in rootLeaves"
              :key="item.key"
              :label="t(item.labelKey)"
              :icon="item.icon"
              :route="item.route"
              :active="leafActive(item)"
            />
          </SidebarSection>

          <SidebarNavGroup
            v-for="group in navGroups"
            :key="group.key"
            :ref="(el) => setGroupRef(group.key, el)"
            :label="t(group.labelKey)"
            :icon="group.icon"
            :active="group.key === activeGroupKey"
          >
            <SidebarItem
              v-for="child in groupChildren(group)"
              :key="child.key"
              :label="t(child.labelKey)"
              :route="child.route"
              :active="leafActive(child)"
            />
          </SidebarNavGroup>
        </div>

        <div class="px-2 pb-2">
          <SidebarCollapseToggle />
        </div>
      </Sidebar>
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
    @logout="onLogout"
  />
  <ForbiddenDialog />
</template>
