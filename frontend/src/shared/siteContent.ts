import { reactive } from 'vue'

export interface SiteContent {
  configuredSections: string[]
  ppdb: Record<string, string>
  contact: Record<string, string>
}

declare global {
  interface Window {
    siteContent?: SiteContent
  }
}

function emptyContent(): SiteContent {
  return {
    configuredSections: [],
    ppdb: { url: '', title: '', lead: '', period: '', hours: '', location: '' },
    contact: {
      address: '', email: '', whatsappUrl: '', whatsappDisplay: '',
      facebookUrl: '', facebookDisplay: '', mapsUrl: '', studentCount: '', staffCount: '',
    },
  }
}

export const siteContent = reactive<SiteContent>(
  (window.siteContent as SiteContent) ?? emptyContent(),
)

function valueAt(path: string): unknown {
  return path.split('.').reduce<unknown>((node, part) => {
    if (node === null || node === undefined) return undefined
    return (node as Record<string, unknown>)[part]
  }, siteContent)
}

/** Admin-authored text with a static locale fallback whenever the field is blank. */
export function contentText(path: string, fallback: string): string {
  const value = valueAt(path)
  return typeof value === 'string' && value.trim() ? value : fallback
}

/** Admin-authored sanitized HTML for v-html sections. */
export function contentHtml(path: string, fallback = ''): string {
  return contentText(path, fallback)
}

/** Literal values (URLs, numbers, display strings). */
export function contentValue(path: string, fallback = ''): string {
  return contentText(path, fallback)
}

export function setSiteContent(next: SiteContent): void {
  for (const key of Object.keys(next)) {
    ;(siteContent as unknown as Record<string, unknown>)[key] = (
      next as unknown as Record<string, unknown>
    )[key]
  }
  window.dispatchEvent(new Event('site-content:updated'))
}
