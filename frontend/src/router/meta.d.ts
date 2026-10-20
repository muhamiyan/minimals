import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    adminOnly?: boolean
    scroll?: boolean
    fullscreen?: boolean
    title?: string
  }
}
