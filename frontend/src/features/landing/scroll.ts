export function scrollToId(id: string): void {
  const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
  document.getElementById(id)?.scrollIntoView({ behavior })
}
