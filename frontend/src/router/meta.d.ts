import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresAdmin?: boolean
    guestOnly?: boolean
    roles?: string[]
    ownerOnly?: boolean
    scroll?: boolean
    fullscreen?: boolean
    title?: string
    description?: string
  }
}
