export interface BreadcrumbItem {
  label: string
  route?: { name: string; params?: Record<string, string> }
  href?: string
  onClick?: (event?: MouseEvent) => void
  [key: string]: unknown
}

export const HOME: BreadcrumbItem = {
  label: 'crumb.dashboard',
  route: { name: 'Dashboard' },
}

interface Crumb {
  label: string
  parent?: BreadcrumbItem
}

export const breadcrumbMap: Record<string, Crumb> = {
  Dashboard: { label: 'crumb.dashboard' },
}
