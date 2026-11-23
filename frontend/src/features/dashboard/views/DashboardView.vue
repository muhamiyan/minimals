<script setup lang="ts">
import { computed } from 'vue'
import { Spinner } from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import AdminDashboardView from './AdminDashboardView.vue'
import SuperadminDashboardView from './SuperadminDashboardView.vue'
import UserDashboardView from './UserDashboardView.vue'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const isSuperadmin = computed(() => auth.user?.appRole === 'superadmin')
const isAdmin = computed(() => {
  const role = auth.user?.appRole
  return role === 'admin' || role === 'superadmin'
})
</script>

<template>
  <AppPageHeader />

  <Spinner v-if="!gateReady" />

  <SuperadminDashboardView v-else-if="isSuperadmin" />
  <AdminDashboardView v-else-if="isAdmin" />
  <UserDashboardView v-else />
</template>
