/**
 * Central API status signaling.
 *
 * The response interceptor maps HTTP error statuses to named
 * window events here instead of dispatching them inline;
 * consumers (router, ForbiddenDialog) listen for the events.
 * Event names follow `api:<status>` (403 → `api:forbidden`),
 * except 401 which keeps the legacy `auth:unauthorized` name
 * the router already listens for.
 */

const EVENT_BY_STATUS: Record<number, string> = {
  401: 'auth:unauthorized',
  403: 'api:forbidden',
}

export function emitApiStatus(status: number): void {
  const name = EVENT_BY_STATUS[status] ?? `api:${status}`
  window.dispatchEvent(new Event(name))
}
