<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage } from 'frappe-ui'

import { useAccountStore } from '@/features/account/store'
import PanelCard from '@/shared/components/PanelCard.vue'
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import StatTile from '@/shared/components/StatTile.vue'
import { useAuthStore } from '@/features/auth/store'
import { getErrorMessage } from '@/shared/api'

const auth = useAuthStore()
const account = useAccountStore()
const { t } = useI18n()

const consoleLinks = [
  { key: 'dash.manageUsers', icon: 'lucide-users', name: 'Users' },
  { key: 'dash.manageBlog', icon: 'lucide-file-text', name: 'BlogAdminList' },
  { key: 'dash.manageActivities', icon: 'lucide-calendar-check', name: 'ActivityAdminList' },
  { key: 'dash.managePrograms', icon: 'lucide-graduation-cap', name: 'ProgramAdminList' },
  { key: 'dash.manageMessages', icon: 'lucide-mail', name: 'ContactAdminList' },
]

const user = computed(() => auth.user)
const userTotal = ref<number | null>(null)
const statsError = ref('')
const statsReady = ref(false)

onMounted(async () => {
  try {
    const [total] = await Promise.all([
      account.fetchUserTotal(),
      auth.fetchRegistrationMode(true),
    ])
    userTotal.value = total
  } catch (e) {
    statsError.value = getErrorMessage(e, t('dash.loadStatsFailed'))
  } finally {
    statsReady.value = true
  }
})
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

    <ShimmerPage v-if="!statsReady" />

    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatTile :label="t('dash.totalUsers')" :value="userTotal" />

        <StatTile :label="t('dash.registration')">
          <Badge
            :label="
              auth.registrationMode === 'closed'
                ? t('dash.registrationClosed')
                : t('dash.registrationOpen')
            "
            :theme="auth.registrationMode === 'closed' ? 'gray' : 'green'"
          />
        </StatTile>
      </div>

      <PanelCard>
        <div>
          <div class="text-base-medium text-ink-gray-8">{{ t('dash.adminConsole') }}</div>
          <p class="mt-1 text-p-sm text-ink-gray-5">{{ t('dash.adminConsoleHint') }}</p>
        </div>
        <div class="mt-4 flex flex-wrap gap-2">
          <Button
            v-for="link in consoleLinks"
            :key="link.name"
            variant="subtle"
            theme="gray"
            :icon-left="link.icon"
            :label="t(link.key)"
            :route="{ name: link.name }"
          />
        </div>
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
    </template>
    <ErrorMessage v-if="statsError" :message="statsError" />
  </div>
</template>
