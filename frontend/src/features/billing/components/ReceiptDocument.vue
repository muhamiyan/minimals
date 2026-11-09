<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Badge } from 'frappe-ui'

import { formatDate, formatRupiah } from '@/shared/format'
import { brand, useBrandLogo } from '@/shared/brand'

import { invoiceStatusLabel, invoiceStatusTheme, type Invoice } from '../store'

const props = defineProps<{
  invoice: Invoice
}>()

const { t } = useI18n()
const { logoSrc, onLogoError } = useBrandLogo()
</script>

<template>
  <div class="invoice-print-root">
    <div class="invoice-print-area space-y-6">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div class="flex items-center gap-3">
        <img v-if="logoSrc" :src="logoSrc" :alt="brand.name" class="h-10 w-10 rounded-4 object-contain" @error="onLogoError" />
        <div>
          <div class="text-xl-semibold text-ink-gray-9">{{ brand.name }}</div>
          <div class="text-p-xs text-ink-gray-5">{{ t('billing.print.title', { number: invoice.number }) }}</div>
        </div>
      </div>
      <Badge
        :label="invoiceStatusLabel(invoice.status)"
        :theme="invoiceStatusTheme(invoice.status)"
        variant="subtle"
      />
    </header>

    <div class="grid gap-4 sm:grid-cols-2">
      <div class="space-y-1">
        <div class="text-p-xs text-ink-gray-5">{{ t('billing.print.organization') }}</div>
        <div class="text-base-medium text-ink-gray-9">{{ invoice.organizationName || '-' }}</div>
      </div>
      <div class="space-y-1">
        <div class="text-p-xs text-ink-gray-5">{{ t('billing.print.tier') }}</div>
        <div class="text-p-sm text-ink-gray-7">{{ invoice.tier }}</div>
      </div>
    </div>

    <table class="invoice-table w-full text-p-sm">
      <tbody>
        <tr>
          <td class="py-3 pr-4 text-ink-gray-5">{{ t('billing.columns.period') }}</td>
          <td class="py-3 text-right text-ink-gray-7 digit-tabular">
            {{ formatDate(invoice.periodStart) }} – {{ formatDate(invoice.periodEnd) }}
          </td>
        </tr>
        <tr>
          <td class="py-3 pr-4 text-ink-gray-5">{{ t('billing.columns.due') }}</td>
          <td class="py-3 text-right text-ink-gray-7 digit-tabular">{{ formatDate(invoice.dueOn) }}</td>
        </tr>
        <tr>
          <td class="py-3 pr-4 text-ink-gray-5">{{ t('billing.print.issued') }}</td>
          <td class="py-3 text-right text-ink-gray-7 digit-tabular">{{ formatDate(invoice.issuedOn) }}</td>
        </tr>
        <tr v-if="invoice.paidOn">
          <td class="py-3 pr-4 text-ink-gray-5">{{ t('billing.print.paid') }}</td>
          <td class="py-3 text-right text-ink-gray-7 digit-tabular">{{ formatDate(invoice.paidOn) }}</td>
        </tr>
        <tr class="invoice-table-amount">
          <td class="py-4 pr-4 text-base-medium text-ink-gray-9">{{ t('billing.columns.amount') }}</td>
          <td class="py-4 text-right text-xl-semibold text-ink-gray-9 digit-tabular">
            {{ formatRupiah(invoice.amount) }}
          </td>
        </tr>
      </tbody>
    </table>

    <footer class="flex flex-wrap items-center justify-between gap-2 text-p-xs text-ink-gray-5">
      <span>{{ invoice.currency }}</span>
      <span v-if="brand.siteUrl">{{ brand.siteUrl }}</span>
    </footer>
    </div>
  </div>
</template>

<style>
.invoice-table {
  border-top: 1px solid var(--outline-gray-1);
  border-bottom: 1px solid var(--outline-gray-1);
}

.invoice-table tbody tr {
  border-bottom: 1px solid var(--outline-gray-1);
}

.invoice-table tbody tr:last-child {
  border-bottom: none;
}

.invoice-table .digit-tabular {
  font-variant-numeric: tabular-nums;
}

@media print {
  /* hide everything except the invoice, keep Dialog ancestors in layout */
  body > #app,
  .dialog-overlay,
  .dialog-scroll-container {
    visibility: hidden !important;
  }

  .invoice-print-root,
  .invoice-print-root * {
    visibility: visible !important;
  }

  .invoice-print-area {
    position: static;
    width: 100%;
    padding: 0;
    background: #fff;
  }

  .dialog-content {
    box-shadow: none !important;
    border: none !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  html, body {
    height: auto !important;
  }

  .invoice-print-area * {
    color: #111 !important;
  }

  .invoice-print-area .text-ink-gray-5,
  .invoice-print-area .text-ink-gray-6,
  .invoice-print-area .text-ink-gray-7 {
    color: #555 !important;
  }

  .invoice-table {
    border-top: 1px solid #ccc;
    border-bottom: 1px solid #ccc;
  }

  .invoice-table tbody tr {
    border-bottom: 1px solid #ccc;
  }
}
</style>
