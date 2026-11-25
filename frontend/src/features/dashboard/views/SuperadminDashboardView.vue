<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ErrorMessage, Spinner } from 'frappe-ui'
import {
  BarChart,
  ChartCard,
  DonutChart,
  NumberCard,
} from 'frappe-ui/charts'

import { formatRupiah } from '@/shared/format'
import { useDashboardStore } from '../store'

const store = useDashboardStore()
const { t, locale } = useI18n()

/** Chart module already measures; a settled plot reads better without a grow-in. */
const flatChartOptions = { animation: false }

const gateReady = computed(() => !!store.stats || !!store.error)

const compactRupiah = (value: number): string =>
  `Rp${new Intl.NumberFormat(locale.value, {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)}`

const monthLabel = (month: string): string =>
  new Date(`${month}-02T00:00:00Z`).toLocaleDateString(locale.value, {
    month: 'short',
    year: '2-digit',
    timeZone: 'UTC',
  })

const organizationsPerMonth = computed(() => {
  const rows = (store.stats?.organizationsPerMonth ?? []).map((row) => ({
    month: monthLabel(row.month),
    count: row.count,
  }))
  return rows.some((row) => row.count > 0) ? rows : []
})

const revenuePerMonth = computed(() => {
  const rows = (store.stats?.revenuePerMonth ?? []).map((row) => ({
    month: monthLabel(row.month),
    amount: row.amount,
  }))
  return rows.some((row) => row.amount > 0) ? rows : []
})

const subscriptionRows = computed(() => {
  const s = store.stats?.subscriptions
  if (!s) return []
  const rows = [
    { status: t('tenancy.status.trial'), count: s.trial },
    { status: t('tenancy.status.active'), count: s.active },
    { status: t('tenancy.status.expired'), count: s.expired },
    { status: t('tenancy.status.cancelled'), count: s.cancelled },
  ]
  return rows.some((row) => row.count > 0) ? rows : []
})

const invoiceRows = computed(() => {
  const i = store.stats?.invoices
  if (!i) return []
  const rows = [
    { status: t('billing.status.issued'), count: i.issued },
    { status: t('billing.status.paid'), count: i.paid },
    { status: t('billing.status.void'), count: i.void },
  ]
  return rows.some((row) => row.count > 0) ? rows : []
})

onMounted(() => {
  store.fetchStats()
})
</script>

<template>
  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <Spinner v-if="!gateReady" class="mx-auto" />

    <template v-else>
      <ErrorMessage v-if="store.error" :message="store.error" />

      <template v-else-if="store.stats">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <NumberCard
            :title="t('dash.super.totalOrganizations')"
            :value="store.stats.organizations.total"
            :loading="store.loading"
          />
          <NumberCard
            :title="t('dash.totalUsers')"
            :value="store.stats.users.total"
            :loading="store.loading"
          />
          <NumberCard
            :title="t('dash.super.revenuePaid')"
            :value="store.stats.revenuePaid"
            :format="formatRupiah"
            :loading="store.loading"
          />
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <ChartCard class="h-80">
            <BarChart
              :title="t('dash.super.orgsPerMonth')"
              :data="organizationsPerMonth"
              x="month"
              y="count"
              :series-config="{
                count: { label: t('dash.super.organizationsSeries') },
              }"
              :echart-options="flatChartOptions"
              :loading="store.loading"
            >
              <template #empty>
                <span class="text-p-sm text-ink-gray-5">
                  {{ t('dash.super.noData') }}
                </span>
              </template>
            </BarChart>
          </ChartCard>
          <ChartCard class="h-80">
            <BarChart
              :title="t('dash.super.revenuePerMonth')"
              :data="revenuePerMonth"
              x="month"
              y="amount"
              :series-config="{
                amount: {
                  label: t('dash.super.revenueSeries'),
                  format: formatRupiah,
                },
              }"
              :y-axis="{ format: compactRupiah }"
              :echart-options="flatChartOptions"
              :loading="store.loading"
            >
              <template #empty>
                <span class="text-p-sm text-ink-gray-5">
                  {{ t('dash.super.noData') }}
                </span>
              </template>
            </BarChart>
          </ChartCard>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <ChartCard class="h-80">
            <DonutChart
              :title="t('dash.super.subscriptionsByStatus')"
              :data="subscriptionRows"
              category="status"
              value="count"
              :center-label="t('dash.super.subscriptionsByStatus')"
              :echart-options="flatChartOptions"
              :loading="store.loading"
            >
              <template #empty>
                <span class="text-p-sm text-ink-gray-5">
                  {{ t('dash.super.noData') }}
                </span>
              </template>
            </DonutChart>
          </ChartCard>
          <ChartCard class="h-80">
            <DonutChart
              :title="t('dash.super.invoicesByStatus')"
              :data="invoiceRows"
              category="status"
              value="count"
              :center-label="t('dash.super.invoicesByStatus')"
              :echart-options="flatChartOptions"
              :loading="store.loading"
            >
              <template #empty>
                <span class="text-p-sm text-ink-gray-5">
                  {{ t('dash.super.noData') }}
                </span>
              </template>
            </DonutChart>
          </ChartCard>
        </div>
      </template>
    </template>
  </div>
</template>
