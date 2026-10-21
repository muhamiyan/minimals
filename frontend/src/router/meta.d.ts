import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    scroll?: boolean
    fullscreen?: boolean
    title?: string
    description?: string
  }
}
