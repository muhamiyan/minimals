<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { Icon, Tooltip } from 'frappe-ui'
import { isNavItemActive } from './nav'
import type { ShellNavItem } from './types'

const props = defineProps<{
  link: ShellNavItem
  collapsed?: boolean
}>()

const route = useRoute()
const router = useRouter()

const isActive = computed(() => isNavItemActive(props.link, route.name))

function handleClick() {
  if (!props.link.to) return
  void router.push(props.link.to as RouteLocationRaw)
}
</script>

<template>
  <button
    type="button"
    class="flex h-7 w-full cursor-pointer items-center rounded text-ink-gray-8 duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 disabled:pointer-events-none"
    :class="isActive ? 'bg-surface-selected shadow-sm' : 'hover:bg-surface-gray-2'"
    :disabled="!link.to"
    :aria-current="isActive ? 'page' : undefined"
    :data-state="isActive ? 'active' : 'inactive'"
    @click="handleClick"
  >
    <div
      class="flex w-full items-center duration-300 ease-in-out"
      :class="collapsed ? 'relative justify-center p-1' : 'px-2 py-1'"
    >
      <Tooltip :text="link.label" placement="right">
        <span class="grid h-5 w-6 flex-shrink-0 place-items-center">
          <Icon :icon="link.icon" class="size-4 text-ink-gray-8" />
        </span>
      </Tooltip>
      <span
        class="flex-shrink-0 text-sm duration-300 ease-in-out"
        :class="collapsed ? 'ms-0 w-0 overflow-hidden opacity-0' : 'ms-2 w-auto opacity-100'"
      >
        {{ link.label }}
      </span>
    </div>
  </button>
</template>
