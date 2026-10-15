<script setup lang="ts">
import { Select, TextInput, type SelectOptionValue } from 'frappe-ui'

const search = defineModel<string>('search', { default: '' })
const perPage = defineModel<number>('perPage', { default: 20 })

withDefaults(
  defineProps<{
    placeholder?: string
    perPageOptions?: { label: string; value: number }[]
    showPerPage?: boolean
  }>(),
  {
    placeholder: 'Search…',
    showPerPage: true,
    perPageOptions: () => [
      { label: '10 / page', value: 10 },
      { label: '20 / page', value: 20 },
      { label: '50 / page', value: 50 },
    ],
  },
)

function onPerPage(value: SelectOptionValue | null | undefined) {
  if (typeof value === 'number') perPage.value = value
}
</script>

<template>
  <div class="flex items-center gap-2">
    <TextInput
      v-model="search"
      type="search"
      :placeholder="placeholder"
      class="w-64"
    />
    <slot />
    <Select
      v-if="showPerPage"
      :model-value="perPage"
      :options="perPageOptions"
      class="ml-auto w-36"
      @update:model-value="onPerPage"
    />
  </div>
</template>
