import type { RouteDestination } from 'frappe-ui'

export interface NavItem {
  key: string
  labelKey: string
  mobileLabelKey?: string
  icon: string
  route: RouteDestination
  requireAdmin?: boolean
  requireSuperadmin?: boolean
  requireOwner?: boolean
  mobile?: boolean
}

export interface MenuPreference {
  order: string[]
  hidden: string[]
}

const NAV_ITEMS: NavItem[] = [
  {
    key: 'Dashboard',
    labelKey: 'nav.dashboard',
    mobileLabelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
  },
  {
    key: 'Users',
    labelKey: 'nav.users',
    icon: 'lucide-users',
    route: { name: 'Users' },
    requireAdmin: true,
  },
  {
    key: 'MyOrganizations',
    labelKey: 'nav.organizations',
    icon: 'lucide-building-2',
    route: { name: 'MyOrganizations' },
  },
  {
    key: 'ToDo',
    labelKey: 'nav.todo',
    icon: 'lucide-list-todo',
    route: { name: 'ToDo' },
  },
  {
    key: 'Plan',
    labelKey: 'nav.plan',
    icon: 'lucide-credit-card',
    route: { name: 'Plan' },
    requireOwner: true,
  },
  {
    key: 'Billing',
    labelKey: 'nav.billing',
    icon: 'lucide-receipt',
    route: { name: 'Billing' },
    requireOwner: true,
  },
  {
    key: 'Plans',
    labelKey: 'nav.plans',
    icon: 'lucide-layout-grid',
    route: { name: 'Plans' },
    requireSuperadmin: true,
  },
  {
    key: 'Tenancy',
    labelKey: 'nav.tenancy',
    icon: 'lucide-building',
    route: { name: 'Tenancy' },
    requireSuperadmin: true,
  },
  {
    key: 'Infrastructure',
    labelKey: 'nav.infrastructure',
    icon: 'lucide-database',
    route: { name: 'Infrastructure' },
    requireSuperadmin: true,
  },
]

export function orderedNavItems(order: string[]): NavItem[] {
  const remaining = new Map(NAV_ITEMS.map((item) => [item.key, item]))
  const ordered: NavItem[] = []

  for (const key of order) {
    const item = remaining.get(key)
    if (!item) continue
    ordered.push(item)
    remaining.delete(key)
  }

  for (const item of NAV_ITEMS) {
    if (remaining.has(item.key)) ordered.push(item)
  }

  return ordered
}

const MAX_MOBILE_NAV_ITEMS = 3

export function mobileNavItems(items: NavItem[]): NavItem[] {
  return items.filter((item) => item.mobile !== false).slice(0, MAX_MOBILE_NAV_ITEMS)
}

export function visibleNavItems(order: string[], hidden: string[]): NavItem[] {
  const hiddenKeys = new Set(hidden)
  return orderedNavItems(order).filter((item) => !hiddenKeys.has(item.key))
}
