import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import { api, getErrorMessage } from '@/shared/api'

export type TursoMode = 'none' | 'embedded_replica' | 'remote'

export interface TursoStatus {
  configured: boolean
  mode: TursoMode
  /** Host of the sync target only — never a credential. */
  syncTarget: string
  tokenConfigured: boolean
  driverInstalled: boolean
}

export interface DatabaseStatus {
  engine: string
  url: string
  turso: TursoStatus
}

export const ENGINE_LABELS: Record<string, string> = {
  sqlite: 'SQLite',
  turso: 'Turso',
  mariadb: 'MariaDB',
  postgresql: 'PostgreSQL',
}

const TURSO_MODE_KEYS: Record<TursoMode, string> = {
  none: 'infra.turso.modeNone',
  embedded_replica: 'infra.turso.modeEmbedded',
  remote: 'infra.turso.modeRemote',
}

export function tursoModeLabel(mode: TursoMode): string {
  return i18n.global.t(TURSO_MODE_KEYS[mode] ?? mode)
}

/** Curated wording for the snake_case keys from `db_error_key()`; null when unknown. */
const DB_ERROR_KEYS = new Set([
  'invalid_db_credentials',
  'db_unreachable',
  'db_not_found',
  'db_timeout',
  'unknown_db_host',
  'db_connection_failed',
  'turso_driver_not_installed',
])

export function dbErrorMessage(key: string): string | null {
  return DB_ERROR_KEYS.has(key) ? i18n.global.t(`infra.errors.${key}`) : null
}

export const useInfraStore = defineStore('infra', () => {
  const status = ref<DatabaseStatus | null>(null)
  const loading = ref(false)
  const error = ref('')

  const testing = ref(false)
  const testError = ref('')
  /** Last successful connection test, as an ISO timestamp. */
  const lastTestedAt = ref<string | null>(null)

  /**
   * `getErrorMessage()` generic-humanizes a key ("Db unreachable"). The
   * connection test returns keys we can say better, so prefer those.
   */
  function testErrorMessage(e: unknown): string {
    const key = (e as { response?: { data?: { message?: unknown } } })?.response?.data
      ?.message
    const known = typeof key === 'string' ? dbErrorMessage(key) : null
    return known ?? getErrorMessage(e, i18n.global.t('infra.errors.connectionFailed'))
  }

  async function fetchStatus(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const { data } = await api.get<DatabaseStatus>('/infra/database')
      status.value = data
    } catch (e: unknown) {
      error.value = getErrorMessage(e, i18n.global.t('infra.errors.loadStatus'))
      status.value = null
    } finally {
      loading.value = false
    }
  }

  async function testConnection(): Promise<boolean> {
    if (testing.value) return false
    testing.value = true
    testError.value = ''
    try {
      await api.post('/infra/database/test')
      lastTestedAt.value = new Date().toISOString()
      return true
    } catch (e: unknown) {
      testError.value = testErrorMessage(e)
      return false
    } finally {
      testing.value = false
    }
  }

  /** Drop state so a re-login never shows the previous user's view. */
  function reset(): void {
    status.value = null
    loading.value = false
    error.value = ''
    testing.value = false
    testError.value = ''
    lastTestedAt.value = null
  }

  return {
    status,
    loading,
    error,
    testing,
    testError,
    lastTestedAt,
    fetchStatus,
    testConnection,
    reset,
  }
})
