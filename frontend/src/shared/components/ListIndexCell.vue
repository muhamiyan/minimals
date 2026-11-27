<script setup lang="ts">
import { ListCell } from 'frappe-ui/list'

defineProps<{
  page: number
  perPage: number
  index: number
}>()
</script>

<template>
  <ListCell>
    <span class="text-p-sm text-ink-gray-5 tabular-nums">
      {{ (page - 1) * perPage + index + 1 }}
    </span>
  </ListCell>
</template>
