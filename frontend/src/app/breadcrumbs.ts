import { SITE_SECTIONS } from '@/features/site-content/sections'

export interface BreadcrumbItem {
  label: string
  route?: { name: string; params?: Record<string, string> }
  href?: string
  onClick?: (event?: MouseEvent) => void
  [key: string]: unknown
}

export const HOME: BreadcrumbItem = {
  label: 'nav.dashboard',
  route: { name: 'Dashboard' },
}

interface Crumb {
  label: string
  parent?: BreadcrumbItem
}

export const breadcrumbMap: Record<string, Crumb> = {
  Dashboard: { label: 'nav.dashboard' },
  Users: { label: 'nav.users' },
  BlogAdminList: { label: 'nav.blog' },
  BlogAdminCreate: {
    label: 'blog.admin.newPost',
    parent: { label: 'nav.blog', route: { name: 'BlogAdminList' } },
  },
  BlogAdminEdit: {
    label: 'blog.admin.editPost',
    parent: { label: 'nav.blog', route: { name: 'BlogAdminList' } },
  },
  ActivityAdminList: { label: 'dash.manageActivities' },
  ActivityAdminCreate: {
    label: 'activity.admin.newActivity',
    parent: { label: 'dash.manageActivities', route: { name: 'ActivityAdminList' } },
  },
  ActivityAdminEdit: {
    label: 'activity.admin.editActivity',
    parent: { label: 'dash.manageActivities', route: { name: 'ActivityAdminList' } },
  },
  ProgramAdminList: { label: 'dash.managePrograms' },
  ProgramAdminCreate: {
    label: 'program.admin.newProgram',
    parent: { label: 'dash.managePrograms', route: { name: 'ProgramAdminList' } },
  },
  ProgramAdminEdit: {
    label: 'program.admin.editProgram',
    parent: { label: 'dash.managePrograms', route: { name: 'ProgramAdminList' } },
  },
  ScholarshipAdminList: { label: 'dash.manageScholarships' },
  ScholarshipAdminCreate: {
    label: 'scholarship.admin.newScholarship',
    parent: { label: 'dash.manageScholarships', route: { name: 'ScholarshipAdminList' } },
  },
  ScholarshipAdminEdit: {
    label: 'scholarship.admin.editScholarship',
    parent: { label: 'dash.manageScholarships', route: { name: 'ScholarshipAdminList' } },
  },
  ContactAdminList: { label: 'dash.manageMessages' },
  ...Object.fromEntries(
    SITE_SECTIONS.map((section) => [
      section.routeName,
      {
        label: section.labelKey,
      },
    ]),
  ),
}
