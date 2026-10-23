<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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
import ForbiddenDialog from '@/shared/components/ForbiddenDialog.vue'
import { brand } from '@/shared/brand'
import { useMediaQuery } from './useMediaQuery'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { t, locale } = useI18n()

const isFullscreen = computed(
  () => route.meta.fullscreen === true || route.query.fullscreen === '1',
)

const isDesktop = useMediaQuery('(min-width: 640px)')

const sidebarCollapsed = ref(false)

const { colorScheme, resolvedColorScheme, setColorScheme, toggleColorScheme } =
  useColorScheme()

const headerMenu = computed(() => [
  {
    group: t('menu.theme'),
    options: [
      {
        label: t('menu.light'),
        icon: 'lucide-sun',
        selected: colorScheme.value === 'light',
        onClick: () => setColorScheme('light'),
      },
      {
        label: t('menu.dark'),
        icon: 'lucide-moon',
        selected: colorScheme.value === 'dark',
        onClick: () => setColorScheme('dark'),
      },
      {
        label: t('menu.system'),
        icon: 'lucide-monitor',
        selected: colorScheme.value === 'system',
        onClick: () => setColorScheme('system'),
      },
    ],
  },
  {
    group: t('menu.language'),
    options: [
      {
        label: 'English',
        icon: 'lucide-languages',
        selected: locale.value === 'en',
        onClick: () => (locale.value = 'en'),
      },
      {
        label: 'Bahasa Indonesia',
        icon: 'lucide-languages',
        selected: locale.value === 'id',
        onClick: () => (locale.value = 'id'),
      },
    ],
  },
  { label: t('menu.logout'), icon: 'lucide-log-out', onClick: onLogout },
])

const themeLabel = computed(() =>
  resolvedColorScheme.value === 'dark' ? t('menu.light') : t('menu.dark'),
)
const themeIcon = computed(() =>
  resolvedColorScheme.value === 'dark' ? 'lucide-sun' : 'lucide-moon',
)

async function onLogout() {
  await auth.logout()
  await router.replace('/login')
}
</script>

<template>
  <router-view v-if="isFullscreen" />

  <DesktopShell
    v-else-if="isDesktop"
    :scroll="route.meta.scroll !== false"
  >
    <template #sidebar>
      <Sidebar v-model:collapsed="sidebarCollapsed" class="border-r">
        <SidebarHeader
          :title="brand.name"
          :subtitle="auth.user?.fullName || auth.user?.email || ''"
          :menu-items="headerMenu"
        />
        <div class="flex-1 overflow-y-auto space-y-0.5 px-2 pb-2">
          <SidebarSection :label="t('menu.section')">
            <SidebarItem
              :label="t('nav.dashboard')"
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
          :label="t('nav.home')"
          icon="lucide-house"
          :route="{ name: 'Dashboard' }"
        />
        <MobileNavItem :label="themeLabel" :icon="themeIcon" @click="toggleColorScheme" />
        <MobileNavItem
          :label="locale === 'en' ? 'Bahasa Indonesia' : 'English'"
          icon="lucide-languages"
          @click="locale = locale === 'en' ? 'id' : 'en'"
        />
        <MobileNavItem :label="t('menu.logout')" icon="lucide-log-out" @click="onLogout" />
      </MobileNav>
    </template>
  </MobileShell>

  <ForbiddenDialog />
</template>
