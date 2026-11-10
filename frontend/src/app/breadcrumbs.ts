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
  ToDo: { label: 'crumb.todo' },
  MyOrganizations: { label: 'crumb.organizations' },
  MyOrganization: {
    label: 'crumb.organization',
    parent: { label: 'crumb.organizations', route: { name: 'MyOrganizations' } },
  },
  Tenancy: { label: 'crumb.tenancy' },
  TenancyOrg: {
    label: 'crumb.organization',
    parent: { label: 'crumb.tenancy', route: { name: 'Tenancy' } },
  },
  Plans: { label: 'crumb.plans' },
  Infrastructure: { label: 'crumb.infrastructure' },
  Billing: { label: 'crumb.billing' },
}
