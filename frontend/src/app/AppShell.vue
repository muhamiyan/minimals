<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  DesktopShell,
  MobileNav,
  MobileNavItem,
  MobileShell,
  Sidebar,
  SidebarCollapseToggle,
  SidebarHeader,
  SidebarItem,
  SidebarSection,
  useColorScheme,
} from 'frappe-ui'

import { useAuthStore } from '@/features/auth/store'
import { useMediaQuery } from './useMediaQuery'

const router = useRouter()
const auth = useAuthStore()

const isDesktop = useMediaQuery('(min-width: 640px)')

const { colorScheme, resolvedColorScheme, setColorScheme, toggleColorScheme } =
  useColorScheme()

const headerMenu = computed(() => [
  {
    group: 'Theme',
    options: [
      {
        label: 'Light',
        icon: 'lucide-sun',
        selected: colorScheme.value === 'light',
        onClick: () => setColorScheme('light'),
      },
      {
        label: 'Dark',
        icon: 'lucide-moon',
        selected: colorScheme.value === 'dark',
        onClick: () => setColorScheme('dark'),
      },
      {
        label: 'System',
        icon: 'lucide-monitor',
        selected: colorScheme.value === 'system',
        onClick: () => setColorScheme('system'),
      },
    ],
  },
  { label: 'Log out', icon: 'lucide-log-out', onClick: onLogout },
])

const themeLabel = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'Light' : 'Dark',
)
const themeIcon = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
)

async function onLogout() {
  await auth.logout()
  router.replace('/login')
}
</script>

<template>
  <DesktopShell v-if="isDesktop">
    <template #sidebar>
      <Sidebar class="border-r">
        <SidebarHeader
          title="Minimals"
          :subtitle="auth.user?.fullName || auth.user?.email || ''"
          :menu-items="headerMenu"
        />
        <div class="flex-1 overflow-y-auto space-y-0.5 px-2 pb-2">
          <SidebarSection label="Menu">
            <SidebarItem
              label="Dashboard"
              icon="lucide-house"
              :route="{ name: 'Dashboard' }"
            />
          </SidebarSection>
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
      <MobileNav>
        <MobileNavItem
          label="Home"
          icon="lucide-house"
          :route="{ name: 'Dashboard' }"
        />
        <MobileNavItem :label="themeLabel" :icon="themeIcon" @click="toggleColorScheme" />
        <MobileNavItem label="Log out" icon="lucide-log-out" @click="onLogout" />
      </MobileNav>
    </template>
  </MobileShell>
</template>
