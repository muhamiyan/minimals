<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { Icon } from 'frappe-ui'
import { isNavItemActive } from './nav'
import type { ShellNavItem } from './types'

const props = defineProps<{
  items: ShellNavItem[]
}>()

const route = useRoute()
const router = useRouter()

const activeName = computed(() => route.name)

function handleClick(item: ShellNavItem) {
  if (!item.to) return
  void router.push(item.to as RouteLocationRaw)
}
</script>

<template>
  <nav
    v-if="props.items.length"
    data-slot="mobile-bottom-nav"
    class="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-outline-gray-2 bg-surface-white pb-[env(safe-area-inset-bottom)]"
  >
    <button
      v-for="item in props.items"
      :key="item.label"
      type="button"
      class="flex flex-1 flex-col items-center justify-center gap-0.5 px-2 py-3 transition active:scale-95 disabled:pointer-events-none"
      :disabled="!item.to"
      :aria-label="item.label"
      :aria-current="isNavItemActive(item, activeName) ? 'page' : undefined"
      :data-state="isNavItemActive(item, activeName) ? 'active' : 'inactive'"
      @click="handleClick(item)"
    >
      <Icon
        :icon="item.icon"
        class="size-6"
        :class="isNavItemActive(item, activeName) ? 'text-ink-blue-6' : 'text-ink-gray-5'"
      />
      <span
        class="max-w-full truncate text-[10px]"
        :class="
          isNavItemActive(item, activeName)
            ? 'font-medium text-ink-blue-6'
            : 'text-ink-gray-6'
        "
      >
        {{ item.label }}
      </span>
    </button>
  </nav>
</template>
