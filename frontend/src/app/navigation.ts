import type { RouteLocationRaw } from 'vue-router'

export interface NavLeaf {
  key: string
  labelKey: string
  mobileLabelKey?: string
  icon: string
  route: RouteLocationRaw
  match: string
  exact?: boolean
  requireAdmin?: boolean
}

export interface NavGroup {
  key: string
  labelKey: string
  icon: string
  requireAdmin?: boolean
  children: NavLeaf[]
}

export type NavRoot = NavLeaf | NavGroup

export interface MenuPreference {
  order: string[]
  hidden: string[]
}

export const NAV_ROOTS: NavRoot[] = [
  {
    key: 'Dashboard',
    labelKey: 'nav.dashboard',
    mobileLabelKey: 'nav.home',
    icon: 'lucide-house',
    route: { name: 'Dashboard' },
    match: '/dashboard',
    exact: true,
  },
  {
    key: 'Users',
    labelKey: 'nav.users',
    icon: 'lucide-users',
    route: { name: 'Users' },
    match: '/users',
    exact: true,
    requireAdmin: true,
  },
  {
    key: 'BlogAdminList',
    labelKey: 'nav.blog',
    icon: 'lucide-newspaper',
    route: { name: 'BlogAdminList' },
    match: '/blog',
    requireAdmin: true,
  },
  {
    key: 'ContactAdminList',
    labelKey: 'dash.manageMessages',
    icon: 'lucide-mail',
    route: { name: 'ContactAdminList' },
    match: '/messages/manage',
    requireAdmin: true,
  },
  {
    key: 'content',
    labelKey: 'nav.managementContent',
    icon: 'lucide-file-text',
    requireAdmin: true,
    children: [
      {
        key: 'ProgramAdminList',
        labelKey: 'dash.managePrograms',
        icon: 'lucide-graduation-cap',
        route: { name: 'ProgramAdminList' },
        match: '/programs',
      },
      {
        key: 'ScholarshipAdminList',
        labelKey: 'dash.manageScholarships',
        icon: 'lucide-award',
        route: { name: 'ScholarshipAdminList' },
        match: '/scholarships',
      },
      {
        key: 'ActivityAdminList',
        labelKey: 'dash.manageActivities',
        icon: 'lucide-calendar-check',
        route: { name: 'ActivityAdminList' },
        match: '/activities',
      },
      {
        key: 'SiteSectionPpdb',
        labelKey: 'siteContent.sections.ppdb',
        icon: 'lucide-graduation-cap',
        route: { name: 'SiteSectionPpdb' },
        match: '/ppdb/manage',
        exact: true,
      },
      {
        key: 'SiteSectionContact',
        labelKey: 'siteContent.sections.contact',
        icon: 'lucide-contact-round',
        route: { name: 'SiteSectionContact' },
        match: '/contact/manage',
        exact: true,
      },
    ],
  },
]

export function isNavGroup(root: NavRoot): root is NavGroup {
  return 'children' in root
}

export function matchesPath(leaf: NavLeaf, path: string): boolean {
  if (leaf.exact) return path === leaf.match
  return path === leaf.match || path.startsWith(leaf.match + '/')
}

export function orderedRoots(order: string[]): NavRoot[] {
  const remaining = new Map(NAV_ROOTS.map((root) => [root.key, root]))
  const ordered: NavRoot[] = []

  for (const key of order) {
    const root = remaining.get(key)
    if (!root) continue
    ordered.push(root)
    remaining.delete(key)
  }

  for (const root of NAV_ROOTS) {
    if (remaining.has(root.key)) ordered.push(root)
  }

  return ordered
}

export function visibleRoots(order: string[], hidden: string[]): NavRoot[] {
  const hiddenKeys = new Set(hidden)
  return orderedRoots(order).filter((root) => !hiddenKeys.has(root.key))
}

export function findActiveGroupKey(groups: NavGroup[], path: string): string | null {
  for (const group of groups) {
    if (group.children.some((child) => matchesPath(child, path))) return group.key
  }
  return null
}

export function flattenLeaves(
  roots: NavRoot[],
  hidden: string[],
  inScope: (node: { requireAdmin?: boolean }) => boolean = () => true,
): NavLeaf[] {
  const hiddenKeys = new Set(hidden)
  const leaves: NavLeaf[] = []
  for (const root of roots) {
    if (isNavGroup(root)) {
      for (const child of root.children) {
        if (inScope(child) && !hiddenKeys.has(child.key)) leaves.push(child)
      }
    } else if (inScope(root) && !hiddenKeys.has(root.key)) {
      leaves.push(root)
    }
  }
  return leaves
}
