<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  TabButtons,
  useColorScheme,
  type ColorScheme,
  type TabButtonValue,
} from 'frappe-ui'

const { t } = useI18n()
const { colorScheme, setColorScheme } = useColorScheme()

const options = computed(() => [
  { value: 'light', label: t('menu.light'), icon: 'lucide-sun' },
  { value: 'dark', label: t('menu.dark'), icon: 'lucide-moon' },
  { value: 'system', label: t('menu.system'), icon: 'lucide-monitor' },
])

function select(value: TabButtonValue) {
  setColorScheme(value as ColorScheme)
}
</script>

<template>
  <TabButtons
    :model-value="colorScheme"
    :options="options"
    :aria-label="t('menu.theme')"
    fluid
    @update:model-value="select"
  />
</template>
