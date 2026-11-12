<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { PageHeader, Spinner } from 'frappe-ui'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'

import AdminDashboardView from './AdminDashboardView.vue'
import UserDashboardView from './UserDashboardView.vue'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const isAdmin = computed(() => auth.user?.appRole === 'admin')

onMounted(async () => {
  if (!auth.checked) await auth.fetchMe()
})
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
  </PageHeader>

  <Spinner v-if="!gateReady" />

  <AdminDashboardView v-else-if="isAdmin" />
  <UserDashboardView v-else />
</template>
