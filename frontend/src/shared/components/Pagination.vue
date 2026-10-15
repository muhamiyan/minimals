<script setup lang="ts">
import { computed } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps<{
  total: number
  page: number
  perPage: number
  always?: boolean
  align?: 'center' | 'end'
}>()

const emit = defineEmits<{
  'update:page': [page: number]
}>()

const pageCount = computed(() =>
  Math.max(1, Math.ceil(props.total / Math.max(1, props.perPage))),
)

const pages = computed<Array<number | 'gap'>>(() => {
  const count = pageCount.value
  const current = Math.min(Math.max(1, props.page), count)
  if (count <= 7) {
    return Array.from({ length: count }, (_, i) => i + 1)
  }
  const items: Array<number | 'gap'> = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(count - 1, current + 1)
  if (start > 2) items.push('gap')
  for (let i = start; i <= end; i++) items.push(i)
  if (end < count - 1) items.push('gap')
  items.push(count)
  return items
})

function go(page: number) {
  if (page !== props.page && page >= 1 && page <= pageCount.value) {
    emit('update:page', page)
  }
}
</script>

<template>
  <nav
    v-if="always || total > perPage"
    :class="[
      'flex items-center gap-1',
      align === 'end' ? 'justify-end' : 'justify-center',
    ]"
    aria-label="Pagination"
  >
    <Button
      variant="ghost"
      theme="gray"
      icon="lucide-chevron-left"
      label="Previous page"
      :disabled="page <= 1"
      @click="go(page - 1)"
    />
    <template v-for="(item, index) in pages" :key="index">
      <Button
        v-if="item !== 'gap'"
        :variant="item === page ? 'solid' : 'outline'"
        theme="gray"
        :label="String(item)"
        @click="go(item)"
      />
      <span v-else class="px-1 text-ink-gray-5">…</span>
    </template>
    <Button
      variant="ghost"
      theme="gray"
      icon="lucide-chevron-right"
      label="Next page"
      :disabled="page >= pageCount"
      @click="go(page + 1)"
    />
  </nav>
</template>
