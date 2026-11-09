<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Dialog, type DialogAction } from 'frappe-ui'

import { type Invoice } from '../store'
import ReceiptDocument from './ReceiptDocument.vue'

const open = defineModel<boolean>('open', { default: false })
const props = defineProps<{
  invoice: Invoice | null
}>()

const { t } = useI18n()

const actions = computed<DialogAction[]>(() => [
  {
    label: t('billing.actions.cancel'),
    variant: 'outline',
    onClick: () => {
      open.value = false
    },
  },
  {
    label: t('billing.actions.print'),
    icon: 'lucide-printer',
    variant: 'solid',
    theme: 'gray',
    onClick: () => {
      if (props.invoice) document.title = props.invoice.number
      window.print()
    },
  },
])
</script>

<template>
  <Dialog
    v-model:open="open"
    :title="props.invoice ? t('billing.print.title', { number: props.invoice.number }) : ''"
    icon="lucide-file-text"
    size="md"
    :actions="actions"
  >
    <ReceiptDocument v-if="props.invoice" :invoice="props.invoice" />
  </Dialog>
</template>
