const idrNumber = new Intl.NumberFormat('id-ID', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})
const idrDate = new Intl.DateTimeFormat('id-ID', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return ''
  const n = typeof value === 'string' ? parseFloat(value) : value
  if (Number.isNaN(n)) return ''
  return idrNumber.format(n)
}

export function formatRupiah(value: number | string | null | undefined): string {
  const formatted = formatNumber(value)
  return formatted ? `Rp ${formatted}` : ''
}

const isoDateOnly = /^\d{4}-\d{2}-\d{2}$/

export function formatDate(value: string | null | undefined): string {
  if (!value) return ''
  // A date-only value is a calendar day, not an instant: anchor it to local
  // midnight so it never shifts a day in negative UTC offsets.
  const d = new Date(isoDateOnly.test(value) ? `${value}T00:00:00` : value)
  return Number.isNaN(d.getTime()) ? '' : idrDate.format(d)
}
