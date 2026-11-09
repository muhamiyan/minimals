import type { RouteDestination } from 'frappe-ui'

export interface NavItem {
  key: string
  labelKey: string
  mobileLabelKey?: string
  icon: string
  route: RouteDestination
  /** Role gate evaluated in menuStore against auth + org membership. */
  gate?: 'superadmin' | 'owner' | 'superadminOrOwner'
  /** Feature flag evaluated in menuStore via tenancy.hasFeature(flag). */
  feature?: string
  /** Domain key evaluated in menuStore via tenancy.domainMode(domain). */
  domain?: string
}

export interface MenuPreference {
  order: string[]
  hidden: string[]
}

export const NAV_ITEMS: NavItem[] = [
  {
    key: 'Dashboard',
    labelKey: 'nav.dashboard',
    mobileLabelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
  },
  {
    key: 'ToDos',
    labelKey: 'nav.todos',
    icon: 'lucide-list-todo',
    route: { name: 'ToDos' },
  },
  {
    key: 'MyOrganizations',
    labelKey: 'nav.organizations',
    icon: 'lucide-building',
    route: { name: 'MyOrganizations' },
    gate: 'owner',
  },
  {
    key: 'Tenancy',
    labelKey: 'nav.tenancy',
    icon: 'lucide-building-2',
    route: { name: 'Tenancy' },
    gate: 'superadmin',
  },
  {
    key: 'Plans',
    labelKey: 'nav.plans',
    icon: 'lucide-layers',
    route: { name: 'Plans' },
    gate: 'superadmin',
    domain: 'plans',
  },
  {
    key: 'Billing',
    labelKey: 'nav.billing',
    icon: 'lucide-credit-card',
    route: { name: 'Billing' },
    gate: 'superadminOrOwner',
    domain: 'billing',
  },
  {
    key: 'Infrastructure',
    labelKey: 'nav.infrastructure',
    icon: 'lucide-database',
    route: { name: 'Infrastructure' },
    gate: 'superadmin',
    domain: 'infra',
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

export function visibleNavItems(order: string[], hidden: string[]): NavItem[] {
  const hiddenKeys = new Set(hidden)
  return orderedNavItems(order).filter((item) => !hiddenKeys.has(item.key))
}
