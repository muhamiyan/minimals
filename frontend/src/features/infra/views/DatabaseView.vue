<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, PageHeader, Spinner, toast } from 'frappe-ui'

import PageBreadcrumbs from '@/shared/components/PageBreadcrumbs.vue'

import { ENGINE_LABELS, tursoModeLabel, useInfraStore } from '../store'

const store = useInfraStore()
const { t, locale } = useI18n()

const engineLabel = computed(() => {
  const engine = store.status?.engine
  return engine ? (ENGINE_LABELS[engine] ?? engine) : ''
})

const engineTheme = computed(() => (store.status?.engine === 'turso' ? 'violet' : 'gray'))

const isTurso = computed(() => store.status?.engine === 'turso')

const turso = computed(() => store.status?.turso ?? null)

const modeLabel = computed(() =>
  turso.value ? tursoModeLabel(turso.value.mode) : '',
)

/** A readiness signal, not just a list of booleans. */
const syncSummary = computed(() => {
  const info = turso.value
  if (!info) return ''
  if (info.mode === 'none') return t('infra.turso.summaryNone')
  const parts: string[] = []
  if (info.mode === 'embedded_replica') {
    parts.push(
      info.syncTarget
        ? t('infra.turso.summarySyncTarget', { target: info.syncTarget })
        : t('infra.turso.summaryNoTarget'),
    )
  } else {
    parts.push(t('infra.turso.summaryDirect'))
  }
  parts.push(
    info.tokenConfigured ? t('infra.turso.tokenSet') : t('infra.turso.tokenMissing'),
  )
  if (!info.driverInstalled) parts.push(t('infra.turso.driverMissing'))
  return parts.join(' ')
})

const testedAt = computed(() => {
  if (!store.lastTestedAt) return ''
  const d = new Date(store.lastTestedAt)
  return Number.isNaN(d.getTime()) ? '' : d.toLocaleTimeString(locale.value)
})

async function runTest(): Promise<void> {
  const ok = await store.testConnection()
  if (ok) toast.success(t('infra.test.ok'))
}

onMounted(() => {
  store.fetchStatus()
})
</script>

<template>
  <PageHeader>
    <PageBreadcrumbs />
  </PageHeader>

  <div class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <div v-if="store.loading && !store.status" class="flex justify-center py-16">
      <Spinner />
    </div>

    <ErrorMessage v-else-if="store.error" :message="store.error" />

    <template v-else-if="store.status">
      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">{{ t('infra.db.title') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('infra.db.description') }}
          </p>
        </div>
        <dl class="grid gap-4 sm:grid-cols-2">
          <div class="space-y-1">
            <dt class="text-p-xs text-ink-gray-5">{{ t('infra.db.engine') }}</dt>
            <dd>
              <Badge :label="engineLabel" :theme="engineTheme" variant="subtle" />
            </dd>
          </div>
          <div class="space-y-1 sm:col-span-2">
            <dt class="text-p-xs text-ink-gray-5">{{ t('infra.db.connection') }}</dt>
            <dd class="break-all text-p-sm text-ink-gray-8">{{ store.status.url }}</dd>
          </div>
        </dl>
      </section>

      <section
        v-if="isTurso"
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="space-y-1">
          <h2 class="text-base-medium text-ink-gray-8">{{ t('infra.turso.title') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('infra.turso.description') }}
          </p>
        </div>

        <div v-if="turso" class="space-y-4">
          <dl class="grid gap-4 sm:grid-cols-2">
            <div class="space-y-1">
              <dt class="text-p-xs text-ink-gray-5">{{ t('infra.turso.mode') }}</dt>
              <dd>
                <Badge
                  :label="modeLabel"
                  :theme="turso.mode === 'none' ? 'gray' : 'violet'"
                  variant="subtle"
                />
              </dd>
            </div>
            <div class="space-y-1">
              <dt class="text-p-xs text-ink-gray-5">{{ t('infra.turso.syncTarget') }}</dt>
              <dd class="text-p-sm text-ink-gray-8">
                {{ turso.syncTarget || '—' }}
              </dd>
            </div>
            <div class="space-y-1">
              <dt class="text-p-xs text-ink-gray-5">{{ t('infra.turso.authToken') }}</dt>
              <dd>
                <Badge
                  :label="
                    turso.tokenConfigured
                      ? t('infra.turso.configured')
                      : t('infra.turso.notSet')
                  "
                  :theme="turso.tokenConfigured ? 'green' : 'amber'"
                  variant="subtle"
                />
              </dd>
            </div>
            <div class="space-y-1">
              <dt class="text-p-xs text-ink-gray-5">{{ t('infra.turso.driver') }}</dt>
              <dd>
                <Badge
                  :label="
                    turso.driverInstalled
                      ? t('infra.turso.installed')
                      : t('infra.turso.missing')
                  "
                  :theme="turso.driverInstalled ? 'green' : 'red'"
                  variant="subtle"
                />
              </dd>
            </div>
          </dl>
          <p v-if="syncSummary" class="text-p-sm text-ink-gray-5">{{ syncSummary }}</p>
        </div>
      </section>

      <section
        class="space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="space-y-1">
            <h2 class="text-base-medium text-ink-gray-8">{{ t('infra.test.title') }}</h2>
            <p class="text-p-sm text-ink-gray-5">
              {{ t('infra.test.description') }}
              <span v-if="testedAt">
                {{ t('infra.test.lastRun', { time: testedAt }) }}
              </span>
            </p>
          </div>
          <Button
            :label="t('infra.test.button')"
            icon-left="lucide-plug-zap"
            variant="outline"
            :loading="store.testing"
            @click="runTest"
          />
        </div>
        <ErrorMessage v-if="store.testError" :message="store.testError" />
      </section>
    </template>
  </div>
</template>
