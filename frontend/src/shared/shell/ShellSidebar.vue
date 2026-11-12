<script setup lang="ts">
import { computed } from 'vue'
import { Tooltip } from 'frappe-ui'
import { filterNavGroups } from './nav'
import SidebarLink from './SidebarLink.vue'
import type { ShellNavGroup } from './types'

const props = withDefaults(
  defineProps<{
    groups: ShellNavGroup[]
    expandLabel?: string
    collapseLabel?: string
  }>(),
  {
    expandLabel: 'Expand',
    collapseLabel: 'Collapse',
  },
)

const collapsed = defineModel<boolean>('collapsed', { default: false })

const visibleGroups = computed(() => filterNavGroups(props.groups))
</script>

<template>
  <div
    class="flex h-full flex-col justify-between overflow-x-hidden border-e bg-surface-menu-bar transition-all duration-300 ease-in-out"
    :class="collapsed ? 'w-14' : 'w-56'"
  >
    <div
      class="flex min-h-0 flex-1 flex-col overflow-y-auto"
      :class="collapsed ? 'items-center' : ''"
    >
      <slot name="header" />
      <div class="flex flex-col">
        <div v-for="group in visibleGroups" :key="group.label" class="mx-2 my-2.5">
          <div
            v-if="!group.hideLabel && !collapsed"
            class="mb-2 mt-3 flex gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
          >
            <span>{{ group.label }}</span>
          </div>
          <nav class="space-y-1">
            <div v-for="item in group.items" :key="item.label">
              <SidebarLink :link="item" :collapsed="collapsed" />
            </div>
          </nav>
        </div>
      </div>
    </div>

    <div class="m-2 flex flex-col gap-1">
      <div
        class="mt-4 flex items-center"
        :class="collapsed ? 'flex-col space-y-3' : 'flex-row'"
      >
        <slot name="footer" />
        <div class="flex-1" />
        <Tooltip :text="collapsed ? expandLabel : collapseLabel">
          <button
            type="button"
            class="cursor-pointer text-ink-gray-7 duration-300 ease-in-out"
            :aria-label="collapsed ? expandLabel : collapseLabel"
            @click="collapsed = !collapsed"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              class="size-4"
              aria-hidden="true"
              :style="{ transform: collapsed ? '' : 'rotateY(180deg)' }"
            >
              <path
                d="M10.875 9.06223L3 9.06232"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M6.74537 5.31699L3 9.06236L6.74527 12.8076"
                stroke="currentColor"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M14.1423 4L14.1423 14.125"
                stroke="currentColor"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </Tooltip>
      </div>
    </div>
  </div>
</template>
