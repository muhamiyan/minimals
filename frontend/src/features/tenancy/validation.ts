import { i18n } from '@/app/i18n'

/** Slug rules mirror `app.tenancy.dto.OrganizationCreateIn`. */
export const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

export function slugify(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/** Returns an error message, or `''` when the slug is acceptable. */
export function validateSlug(value: string): string {
  const slug = value.trim().toLowerCase()
  if (!slug) return i18n.global.t('tenancy.validation.slugRequired')
  if (!SLUG_PATTERN.test(slug)) return i18n.global.t('tenancy.validation.slugPattern')
  return ''
}

/** Returns an error message, or `''` when the name is acceptable. */
export function validateName(value: string): string {
  return value.trim() ? '' : i18n.global.t('tenancy.validation.nameRequired')
}

export function capitalize(value: string): string {
  return value ? value[0].toUpperCase() + value.slice(1) : value
}

/** `advanced_reporting` -> `Advanced reporting`. */
export function humanize(value: string): string {
  const text = value.replace(/_/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** Known feature flags get a translated label; unknown ones fall back to a humanized key. */
export function featureLabel(flag: string): string {
  const key = `tenancy.features.${flag}`
  return i18n.global.te(key) ? i18n.global.t(key) : humanize(flag)
}
