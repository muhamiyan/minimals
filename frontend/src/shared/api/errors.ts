export function getErrorMessage(e: any, fallback = 'An error occurred'): string {
  const message = e?.response?.data?.message
  if (typeof message !== 'string' || !message) return fallback
  return message.replace(/_/g, ' ').replace(/^./, (c: string) => c.toUpperCase())
}
