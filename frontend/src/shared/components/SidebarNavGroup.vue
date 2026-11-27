<script setup lang="ts">
import { computed, inject, ref } from 'vue'
import { SidebarItem, sidebarCollapsedKey, sidebarToggleKey } from 'frappe-ui'

const props = defineProps<{
  label: string
  icon: string
  active?: boolean
}>()

const expanded = ref(props.active ?? false)

const isSidebarCollapsed = inject(
  sidebarCollapsedKey,
  computed(() => false),
)
const toggleSidebar = inject(sidebarToggleKey, () => {})

function toggle() {
  if (isSidebarCollapsed.value) {
    toggleSidebar()
    expanded.value = true
    return
  }
  expanded.value = !expanded.value
}

function expand() {
  expanded.value = true
}

defineExpose({ expand })
</script>

<template>
  <div data-slot="sidebar-nav-group">
    <SidebarItem
      :label="label"
      :icon="icon"
      :aria-expanded="expanded && !isSidebarCollapsed"
      class="hover:!bg-transparent"
      @click="toggle"
    >
      <template #suffix>
        <span
          class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5 transition-transform duration-300 ease-in-out"
          :class="expanded ? '' : '-rotate-90'"
          aria-hidden="true"
        />
      </template>
    </SidebarItem>

    <transition
      enter-active-class="duration-300 ease-in"
      leave-active-class="duration-300 ease-[cubic-bezier(0,1,0.5,1)]"
      enter-to-class="max-h-[600px] overflow-hidden"
      leave-from-class="max-h-[600px] overflow-hidden"
      enter-from-class="max-h-0 overflow-hidden"
      leave-to-class="max-h-0 overflow-hidden"
    >
      <div
        v-show="expanded && !isSidebarCollapsed"
        role="group"
        :aria-label="label"
        class="flex flex-col gap-0.5 pl-4"
      >
        <slot />
      </div>
    </transition>
  </div>
</template>
