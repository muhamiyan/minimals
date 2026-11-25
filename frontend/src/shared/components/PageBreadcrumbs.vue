<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Breadcrumbs, Button } from 'frappe-ui'

import { breadcrumbMap, type BreadcrumbItem, HOME } from '@/app/breadcrumbs'

const props = defineProps<{
  title?: string
}>()

const route = useRoute()
const { t, te } = useI18n()

const crumbs = computed<BreadcrumbItem[]>(() => {
  const entry = breadcrumbMap[route.name as string]
  if (!entry) return []
  return [
    ...(entry.parent ? [{ ...entry.parent, label: t(entry.parent.label) }] : []),
    { label: props.title || t(entry.label) },
  ]
})

const fallbackTitle = computed(() => {
  const name = String(route.name ?? '')
  const key = `route.${name}.title`
  if (name && te(key)) return t(key)
  return typeof route.meta.title === 'string' ? route.meta.title : ''
})
</script>

<template>
  <nav aria-label="Breadcrumb" class="min-w-0">
    <div class="flex min-w-0 items-center">
      <Button
        variant="ghost"
        icon="lucide-home"
        :label="t('crumb.dashboard')"
        :route="HOME.route"
        :tooltip="t('crumb.dashboard')"
      />
      <span
        v-if="crumbs.length"
        class="mx-0.5 text-base text-ink-gray-4"
        aria-hidden="true"
      >
        /
      </span>
      <Breadcrumbs v-if="crumbs.length" :items="crumbs" />
      <span
        v-else-if="fallbackTitle"
        class="text-base-medium text-ink-gray-8"
      >
        {{ fallbackTitle }}
      </span>
    </div>
  </nav>
</template>
