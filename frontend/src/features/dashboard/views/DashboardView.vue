<script setup lang="ts">
import { Badge, PageHeader } from 'frappe-ui'
import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'

import { useAuthStore } from '@/features/auth/store'

const auth = useAuthStore()
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
  </PageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div class="space-y-1 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <p class="text-p-sm text-ink-gray-5">Welcome back</p>
      <div class="text-xl-semibold text-ink-gray-8">
        {{ auth.user?.fullName || auth.user?.username }}
      </div>
      <p class="text-p-sm text-ink-gray-5">{{ auth.user?.email }}</p>
    </div>

    <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
      <div class="text-base-medium text-ink-gray-8">Roles</div>
      <div class="mt-3 flex flex-wrap gap-2">
        <Badge v-if="auth.user?.appRole" :label="auth.user.appRole" />
        <Badge v-for="role in auth.user?.roles ?? []" :key="role" :label="role" />
        <p
          v-if="!auth.user?.appRole && !auth.user?.roles?.length"
          class="text-p-sm text-ink-gray-5"
        >
          No roles assigned
        </p>
      </div>
    </div>
  </div>
</template>
