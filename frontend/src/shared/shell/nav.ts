import type { ShellNavGroup, ShellNavItem } from './types'

export function filterNavGroups(groups: ShellNavGroup[]): ShellNavGroup[] {
  return groups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) => (item.condition ? item.condition() : true)),
    }))
    .filter((group) => group.items.length > 0)
}

export function isNavItemActive(
  item: ShellNavItem,
  currentName?: string | symbol | null,
): boolean {
  const name = currentName == null ? '' : String(currentName)
  if (item.activeFor?.includes(name)) return true
  const target = typeof item.to === 'string' ? item.to : item.to?.name
  return target != null && String(target) === name
}
