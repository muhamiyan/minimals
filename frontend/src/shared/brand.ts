import { computed, reactive, ref, watch } from 'vue'

interface Brand {
  name: string
  tagline: string
  description: string
  siteUrl: string
  logoUrl: string
}

export type BrandMeta = Pick<Brand, 'name' | 'tagline' | 'description' | 'siteUrl'>
export type LogoTone = 'light' | 'dark' | 'opaque' | ''

declare global {
  interface Window {
    brand?: Brand
  }
}

const DEFAULT_BRAND: Brand = {
  name: 'Yayasan Islam Selaparang',
  tagline: '',
  description: '',
  siteUrl: '',
  logoUrl: '',
}

const injected = window.brand

export const brand = reactive<Brand>({
  name: injected?.name?.trim() || DEFAULT_BRAND.name,
  tagline: injected?.tagline ?? '',
  description: injected?.description ?? '',
  siteUrl: injected?.siteUrl ?? '',
  logoUrl: injected?.logoUrl ?? '',
})

export function setBrandLogo(url: string) {
  brand.logoUrl = url
}

export function setBrandMeta(meta: BrandMeta) {
  brand.name = meta.name
  brand.tagline = meta.tagline
  brand.description = meta.description
  brand.siteUrl = meta.siteUrl
  applyFavicon()
  window.dispatchEvent(new Event('brand:updated'))
}

function detectLogoTone(image: HTMLImageElement): LogoTone {
  try {
    const width = Math.max(1, Math.min(64, image.naturalWidth))
    const height = Math.max(1, Math.min(64, image.naturalHeight))
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return ''
    ctx.drawImage(image, 0, 0, width, height)
    const pixels = ctx.getImageData(0, 0, width, height).data

    let alphaTotal = 0
    let luminanceTotal = 0
    let opaquePixels = 0
    for (let i = 0; i < pixels.length; i += 4) {
      const alpha = pixels[i + 3] / 255
      if (alpha < 0.1) continue
      alphaTotal += alpha
      luminanceTotal +=
        alpha *
        (0.2126 * pixels[i] + 0.7152 * pixels[i + 1] + 0.0722 * pixels[i + 2]) /
        255
      if (alpha > 0.95) opaquePixels += 1
    }
    if (!alphaTotal) return ''

    const coverage = opaquePixels / (width * height)
    if (coverage > 0.85) return 'opaque'
    return luminanceTotal / alphaTotal > 0.6 ? 'light' : 'dark'
  } catch {
    return ''
  }
}

function defaultFavicon(): string {
  const initial = (brand.name.trim()[0] || 'Y')
    .toUpperCase()
    .replace(/[&<>"']/g, (char) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' })[char] || char,
    )
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">' +
    '<rect width="64" height="64" rx="12" fill="#0b5c3f"/>' +
    `<text x="32" y="44" text-anchor="middle" font-family="sans-serif" ` +
    `font-size="36" font-weight="700" fill="#ffffff">${initial}</text>` +
    '</svg>'
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

function logoFavicon(image: HTMLImageElement, tone: LogoTone): string {
  const size = 64
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) return defaultFavicon()

  if (tone === 'light') {
    ctx.fillStyle = '#0b5c3f'
    ctx.fillRect(0, 0, size, size)
  } else if (tone === 'dark') {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, size, size)
  }

  const padding = tone === 'opaque' ? 0 : 8
  const scale = Math.min(
    (size - padding * 2) / image.naturalWidth,
    (size - padding * 2) / image.naturalHeight,
  )
  const width = image.naturalWidth * scale
  const height = image.naturalHeight * scale
  ctx.drawImage(image, (size - width) / 2, (size - height) / 2, width, height)
  return canvas.toDataURL('image/png')
}

function applyFavicon(image?: HTMLImageElement, tone: LogoTone = ''): void {
  const icon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
  if (!icon) return
  icon.href = image ? logoFavicon(image, tone) : defaultFavicon()
}

watch(
  () => brand.logoUrl,
  (url) => {
    if (!url) {
      applyFavicon()
      return
    }
    const image = new Image()
    image.onload = () => applyFavicon(image, detectLogoTone(image))
    image.onerror = () => applyFavicon()
    image.src = url
  },
  { immediate: true },
)

/** Backdrop that keeps both light and dark logos visible in either theme. */
export function logoBackdropClass(tone: LogoTone): string {
  if (tone === 'light') return 'bg-surface-gray-9 dark:bg-surface-gray-2'
  if (tone === 'dark') return 'bg-surface-gray-2 dark:bg-surface-gray-10'
  return 'bg-surface-gray-2'
}

/**
 * Logo URL that falls back to empty when the image fails to load, plus the
 * detected tone so surfaces can choose a contrasting backdrop.
 */
export function useBrandLogo() {
  const failed = ref(false)
  const tone = ref<LogoTone>('')

  watch(
    () => brand.logoUrl,
    (url) => {
      failed.value = false
      tone.value = ''
      if (!url) return
      const image = new Image()
      image.onload = () => {
        tone.value = detectLogoTone(image)
      }
      image.onerror = () => {
        failed.value = true
      }
      image.src = url
    },
    { immediate: true },
  )

  const logoSrc = computed(() =>
    brand.logoUrl && !failed.value ? brand.logoUrl : '',
  )
  function onLogoError() {
    failed.value = true
  }
  return { logoSrc, logoTone: tone, onLogoError }
}
