import { i18n } from '@/app/i18n'

export function getErrorMessage(e: any, fallback?: string): string {
  const { t, te } = i18n.global
  const message = e?.response?.data?.message
  if (typeof message !== 'string' || !message) {
    if (fallback !== undefined) return fallback
    return te('error.generic') ? t('error.generic') : 'An error occurred'
  }
  const key = `error.${message}`
  if (te(key)) return t(key)
  return message.replace(/_/g, ' ').replace(/^./, (c: string) => c.toUpperCase())
}
