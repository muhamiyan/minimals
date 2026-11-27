export interface SiteSectionRoute {
  key: string
  routeName: string
  labelKey: string
  sectionKeys: string[]
}

export const SITE_SECTIONS: SiteSectionRoute[] = [
  { key: 'ppdb', routeName: 'SiteSectionPpdb', labelKey: 'siteContent.sections.ppdb', sectionKeys: ['ppdb'] },
  { key: 'contact', routeName: 'SiteSectionContact', labelKey: 'siteContent.sections.contact', sectionKeys: ['contact'] },
]

export function sectionByKey(key: string): SiteSectionRoute | undefined {
  return SITE_SECTIONS.find((section) => section.key === key)
}
