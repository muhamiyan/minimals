<script setup lang="ts">
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { computed } from 'vue'


import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import AdminDashboardView from './AdminDashboardView.vue'
import UserDashboardView from './UserDashboardView.vue'
import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()

const gateReady = computed(() => auth.checked)
const isAdmin = computed(() => auth.user?.appRole === 'admin')
</script>

<template>
  <AppPageHeader />

  <ShimmerPage v-if="!gateReady" />

  <AdminDashboardView v-else-if="isAdmin" />
  <UserDashboardView v-else />
</template>
