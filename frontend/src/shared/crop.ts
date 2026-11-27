interface CropWindow {
  cx: number
  cy: number
  sx: number
  sy: number
  sw: number
  sh: number
  scale: number
  dx: number
  dy: number
  dw: number
  dh: number
}

const MIN_ZOOM = 0.2

const NO_WINDOW: CropWindow = {
  cx: 0.5,
  cy: 0.5,
  sx: 0,
  sy: 0,
  sw: 0,
  sh: 0,
  scale: 0,
  dx: 0,
  dy: 0,
  dw: 0,
  dh: 0,
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high)
}

function clampCenter(value: number, share: number): number {
  if (!Number.isFinite(value)) return 0.5
  const low = share
  const high = 1 - share
  if (high < low) return 0.5
  return clamp(value, low, high)
}

/**
 * Free-zoom crop window. `zoom` is a multiplier of the fit scale, so values
 * below 1 show the whole image inside the crop frame (letterboxed).
 * `aspect` is output width / height.
 */
export function cropWindow(
  cx: number,
  cy: number,
  srcW: number,
  srcH: number,
  stage: number,
  zoom: number,
  aspect = 1,
): CropWindow {
  if (!(srcW > 0) || !(srcH > 0) || !(stage > 0) || !(aspect > 0)) {
    return { ...NO_WINDOW }
  }

  const stageH = stage / aspect
  const fitScale = Math.min(stage / srcW, stageH / srcH)
  const scale = fitScale * Math.max(zoom, MIN_ZOOM)
  const destW = srcW * scale
  const destH = srcH * scale

  const shareX = Math.min(0.5, stage / (2 * scale) / srcW)
  const shareY = Math.min(0.5, stageH / (2 * scale) / srcH)
  const x = clampCenter(cx, shareX)
  const y = clampCenter(cy, shareY)

  const sx = clamp(x * srcW - stage / (2 * scale), 0, Math.max(0, srcW - stage / scale))
  const sy = clamp(
    y * srcH - stageH / (2 * scale),
    0,
    Math.max(0, srcH - stageH / scale),
  )
  const sw = Math.min(srcW - sx, stage / scale)
  const sh = Math.min(srcH - sy, stageH / scale)

  return {
    cx: x,
    cy: y,
    sx,
    sy,
    sw,
    sh,
    scale,
    dx: stage / 2 - x * destW,
    dy: stageH / 2 - y * destH,
    dw: destW,
    dh: destH,
  }
}

export function outputDimensions(sw: number, aspect = 1): { width: number; height: number } {
  if (!Number.isFinite(sw) || sw <= 0 || !(aspect > 0)) return { width: 1, height: 1 }
  const width = Math.min(512, Math.max(1, Math.round(sw)))
  return { width, height: Math.max(1, Math.round(width / aspect)) }
}

export function outputSize(sw: number): number {
  return outputDimensions(sw, 1).width
}
