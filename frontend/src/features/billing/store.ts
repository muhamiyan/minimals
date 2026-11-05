import { defineStore } from 'pinia'
import { ref } from 'vue'

import { i18n } from '@/app/i18n'
import type { Organization } from '@/features/tenancy/store'
import { api, getErrorMessage } from '@/shared/api'

export type BadgeTheme = 'gray' | 'blue' | 'green' | 'red' | 'violet'

const INVOICE_STATUSES = new Set(['issued', 'paid', 'void'])

const INVOICE_STATUS_THEMES: Record<string, BadgeTheme> = {
  issued: 'blue',
  paid: 'green',
  void: 'gray',
}

export function invoiceStatusLabel(status: string): string {
  if (!INVOICE_STATUSES.has(status)) return status
  return i18n.global.t(`billing.status.${status}`)
}

export function invoiceStatusTheme(status: string): BadgeTheme {
  return INVOICE_STATUS_THEMES[status] ?? 'gray'
}

export interface Invoice {
  id: string
  organizationId: string
  organizationName: string
  number: string
  tier: string
  amount: number
  currency: string
  status: string
  periodStart: string
  periodEnd: string
  issuedOn: string
  dueOn: string
  /** Absent on the wire until the invoice is paid (exclude_none). */
  paidOn?: string | null
}

export interface OrgOption {
  id: string
  name: string
  tier: string | null
  startedOn: string | null
  durationValue: number
  durationUnit: string
  /** Null when the plan is billed manually or the org has no subscription. */
  planPrice: number | null
}

export interface BillingSettings {
  trialDays: number
  invoiceLeadDays: number
}

export interface InvoiceInput {
  organizationId: string
  periodStart: string
  amount?: number
}

// Billing periods are anchored to the subscription's UTC creation instant;
// all date math here stays in UTC so a local offset cannot shift the month.
function addMonths(date: Date, months: number): Date {
  const index = date.getUTCMonth() + months
  const year = date.getUTCFullYear() + Math.floor(index / 12)
  const month = ((index % 12) + 12) % 12
  const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate()
  return new Date(Date.UTC(year, month, Math.min(date.getUTCDate(), lastDay)))
}

function toDateInput(date: Date): string {
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  const day = String(date.getUTCDate()).padStart(2, '0')
  return `${date.getUTCFullYear()}-${month}-${day}`
}

/** First billing anniversary strictly after today, as a `YYYY-MM-DD` value. */
export function nextPeriodStart(
  startedOn: string | null | undefined,
  durationValue = 1,
  durationUnit = 'months',
  today = new Date(),
): string {
  const todayUtc = new Date(
    Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()),
  )
  const fallback = toDateInput(
    new Date(Date.UTC(todayUtc.getUTCFullYear(), todayUtc.getUTCMonth() + 1, 1)),
  )
  if (!startedOn) return fallback
  const parsed = new Date(startedOn)
  if (Number.isNaN(parsed.getTime())) return fallback
  const anchor = new Date(
    Date.UTC(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate()),
  )
  const step = Number.isInteger(durationValue) && durationValue > 0 ? durationValue : 1

  if (durationUnit === 'days') {
    const day = 86_400_000
    let steps = Math.floor((todayUtc.getTime() - anchor.getTime()) / (day * step))
    if (anchor.getTime() + steps * step * day > todayUtc.getTime()) steps -= 1
    return toDateInput(new Date(anchor.getTime() + (steps + 1) * step * day))
  }

  const diff =
    (todayUtc.getUTCFullYear() - anchor.getUTCFullYear()) * 12 +
    (todayUtc.getUTCMonth() - anchor.getUTCMonth())
  let steps = Math.floor(diff / step)
  if (addMonths(anchor, steps * step) > todayUtc) steps -= 1
  return toDateInput(addMonths(anchor, (steps + 1) * step))
}

interface Paged<T> {
  items: T[]
  total: number
  page: number
  perPage: number
}

function toOrgOption(org: Organization): OrgOption {
  const sub = org.subscription
  return {
    id: org.id,
    name: org.name,
    tier: sub?.tier ?? null,
    startedOn: sub?.startedOn ?? null,
    durationValue: sub?.planDurationValue ?? 1,
    durationUnit: sub?.planDurationUnit ?? 'months',
    planPrice: sub?.planPrice ?? null,
  }
}

export const useBillingStore = defineStore('billing', () => {
  const items = ref<Invoice[]>([])
  const total = ref(0)
  const page = ref(1)
  const listLoading = ref(false)
  const listError = ref('')
  let listSeq = 0
  const actionError = ref('')
  /** Invoice currently being paid/voided, for row-level loading state. */
  const actingId = ref<string | null>(null)

  // superadmin's organization filter options
  const orgOptions = ref<OrgOption[]>([])

  // create-dialog organization search; kept apart from `orgOptions` so a
  // search result never truncates the filter dropdown's list
  const orgSearchResults = ref<OrgOption[]>([])
  const orgSearchLoading = ref(false)
  let orgSearchSeq = 0

  // superadmin: manual invoice + platform settings
  const createError = ref('')
  const creatingInvoice = ref(false)
  const settingsLoading = ref(false)
  const settingsError = ref('')
  const settingsSaving = ref(false)
  const settingsSaveError = ref('')

  // tenant-facing per-organization list (owner card)
  const orgInvoices = ref<Invoice[]>([])
  const orgInvoicesLoading = ref(false)
  const orgInvoicesError = ref('')
  // Stale-response guard: switching owner orgs must not let a late
  // response overwrite the list of the org the user moved on to.
  let orgInvoicesSeq = 0

  async function fetchList(query: {
    search: string
    perPage: number
    status?: string
    orgId?: string
  }): Promise<void> {
    const seq = ++listSeq
    listLoading.value = true
    listError.value = ''
    try {
      const { data } = await api.get<Paged<Invoice>>('/billing/invoices', {
        params: {
          search: query.search.trim() || undefined,
          status: query.status || undefined,
          orgId: query.orgId || undefined,
          page: page.value,
          per_page: query.perPage,
        },
      })
      if (seq !== listSeq) return
      items.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? page.value
    } catch (e: any) {
      if (seq !== listSeq) return
      listError.value = getErrorMessage(e, i18n.global.t('billing.errors.loadInvoices'))
      items.value = []
      total.value = 0
    } finally {
      if (seq === listSeq) listLoading.value = false
    }
  }

  function setPage(next: number): void {
    page.value = next
  }

  /** Organization names for the superadmin filter dropdown. */
  async function fetchOrgOptions(): Promise<void> {
    try {
      const { data } = await api.get<Paged<Organization>>('/tenancy/organizations', {
        params: { page: 1, per_page: 100 },
      })
      orgOptions.value = (data.items ?? []).map(toOrgOption)
    } catch {
      orgOptions.value = []
    }
  }

  /** Server-side organization search for the create-invoice combobox. */
  async function searchOrgOptions(search: string): Promise<void> {
    const seq = ++orgSearchSeq
    orgSearchLoading.value = true
    try {
      const { data } = await api.get<Paged<Organization>>('/tenancy/organizations', {
        params: { page: 1, per_page: 20, search: search.trim() || undefined },
      })
      if (seq !== orgSearchSeq) return
      orgSearchResults.value = (data.items ?? []).map(toOrgOption)
    } catch {
      if (seq !== orgSearchSeq) return
      orgSearchResults.value = []
    } finally {
      if (seq === orgSearchSeq) orgSearchLoading.value = false
    }
  }

  async function createInvoice(payload: InvoiceInput): Promise<Invoice | null> {
    createError.value = ''
    creatingInvoice.value = true
    try {
      const { data } = await api.post<Invoice>('/billing/invoices', payload)
      return data
    } catch (e: any) {
      createError.value = getErrorMessage(e, i18n.global.t('billing.errors.createInvoice'))
      return null
    } finally {
      creatingInvoice.value = false
    }
  }

  async function fetchSettings(): Promise<BillingSettings | null> {
    settingsLoading.value = true
    settingsError.value = ''
    settingsSaveError.value = ''
    try {
      const { data } = await api.get<BillingSettings>('/billing/settings')
      return data
    } catch (e: any) {
      settingsError.value = getErrorMessage(e, i18n.global.t('billing.errors.loadSettings'))
      return null
    } finally {
      settingsLoading.value = false
    }
  }

  async function saveSettings(payload: Partial<BillingSettings>): Promise<boolean> {
    settingsSaveError.value = ''
    settingsSaving.value = true
    try {
      await api.put<BillingSettings>('/billing/settings', payload)
      return true
    } catch (e: any) {
      settingsSaveError.value = getErrorMessage(e, i18n.global.t('billing.errors.saveSettings'))
      return false
    } finally {
      settingsSaving.value = false
    }
  }

  function replaceItem(updated: Invoice): void {
    const index = items.value.findIndex((invoice) => invoice.id === updated.id)
    if (index !== -1) items.value[index] = updated
  }

  async function markPaid(invoiceId: string, amount?: number): Promise<boolean> {
    actionError.value = ''
    actingId.value = invoiceId
    try {
      const { data } = await api.post<Invoice>(
        `/billing/invoices/${invoiceId}/pay`,
        amount === undefined ? {} : { amount },
      )
      replaceItem(data)
      return true
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('billing.errors.markPaid'))
      return false
    } finally {
      actingId.value = null
    }
  }

  async function voidInvoice(invoiceId: string): Promise<boolean> {
    actionError.value = ''
    actingId.value = invoiceId
    try {
      const { data } = await api.post<Invoice>(`/billing/invoices/${invoiceId}/void`)
      replaceItem(data)
      return true
    } catch (e: any) {
      actionError.value = getErrorMessage(e, i18n.global.t('billing.errors.voidInvoice'))
      return false
    } finally {
      actingId.value = null
    }
  }

  async function fetchOrgInvoices(orgId: string): Promise<void> {
    if (!orgId) return
    const seq = ++orgInvoicesSeq
    orgInvoicesLoading.value = true
    orgInvoicesError.value = ''
    orgInvoices.value = []
    try {
      const { data } = await api.get<Paged<Invoice>>(
        `/billing/organizations/${orgId}/invoices`,
      )
      if (seq !== orgInvoicesSeq) return
      orgInvoices.value = data.items ?? []
    } catch (e: any) {
      if (seq !== orgInvoicesSeq) return
      orgInvoicesError.value = getErrorMessage(e, i18n.global.t('billing.errors.loadInvoices'))
    } finally {
      if (seq === orgInvoicesSeq) orgInvoicesLoading.value = false
    }
  }

  /** Empty the owner card (org switched away or demoted from owner). */
  function clearOrgInvoices(): void {
    orgInvoicesSeq++
    orgInvoices.value = []
    orgInvoicesLoading.value = false
    orgInvoicesError.value = ''
  }

  function reset(): void {
    listSeq++
    orgInvoicesSeq++
    orgSearchSeq++
    items.value = []
    total.value = 0
    page.value = 1
    listLoading.value = false
    listError.value = ''
    actionError.value = ''
    actingId.value = null
    orgOptions.value = []
    orgSearchResults.value = []
    orgSearchLoading.value = false
    createError.value = ''
    creatingInvoice.value = false
    settingsLoading.value = false
    settingsError.value = ''
    settingsSaving.value = false
    settingsSaveError.value = ''
    orgInvoices.value = []
    orgInvoicesLoading.value = false
    orgInvoicesError.value = ''
  }

  return {
    items,
    total,
    page,
    listLoading,
    listError,
    actionError,
    actingId,
    orgOptions,
    orgSearchResults,
    orgSearchLoading,
    createError,
    creatingInvoice,
    settingsLoading,
    settingsError,
    settingsSaving,
    settingsSaveError,
    orgInvoices,
    orgInvoicesLoading,
    orgInvoicesError,
    fetchList,
    setPage,
    fetchOrgOptions,
    searchOrgOptions,
    createInvoice,
    fetchSettings,
    saveSettings,
    markPaid,
    voidInvoice,
    fetchOrgInvoices,
    clearOrgInvoices,
    reset,
  }
})
