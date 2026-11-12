import type { RouteDestination } from 'frappe-ui'

export interface ShellNavItem {
  label: string
  icon: string
  to?: RouteDestination
  activeFor?: string[]
  condition?: () => boolean
}

export interface ShellNavGroup {
  label: string
  hideLabel?: boolean
  items: ShellNavItem[]
}
