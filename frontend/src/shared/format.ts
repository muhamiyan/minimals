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

export function formatDate(value: string | null | undefined): string {
  if (!value) return ''
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '' : idrDate.format(d)
}
