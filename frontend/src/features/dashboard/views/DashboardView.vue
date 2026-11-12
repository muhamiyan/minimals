<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { PageHeader, Spinner } from 'frappe-ui'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'

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

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
})
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
  </PageHeader>

  <Spinner v-if="!gateReady" />

  <SuperadminDashboardView v-else-if="isSuperadmin" />
  <AdminDashboardView v-else-if="isAdmin" />
  <UserDashboardView v-else />
</template>
