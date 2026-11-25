export const GITHUB_URL = 'https://github.com/nusalargepelago'
export const FLAGSHIP_URL = 'https://github.com/nusalargepelago/tantanganbebras'

export const navLinks = [
  { id: 'about', key: 'landing.nav.about' },
  { id: 'program', key: 'landing.nav.program' },
  { id: 'resources', key: 'landing.nav.resources' },
  { id: 'partnership', key: 'landing.nav.partnership' },
  { id: 'contact', key: 'landing.nav.contact' },
]

export interface LoopStep {
  icon: string
  title: string
  desc: string
}

export const loopSteps: LoopStep[] = [
  {
    icon: 'lucide-microscope',
    title: 'landing.loop.steps.research.title',
    desc: 'landing.loop.steps.research.desc',
  },
  {
    icon: 'lucide-code-2',
    title: 'landing.loop.steps.engineering.title',
    desc: 'landing.loop.steps.engineering.desc',
  },
  {
    icon: 'lucide-hand-heart',
    title: 'landing.loop.steps.outreach.title',
    desc: 'landing.loop.steps.outreach.desc',
  },
]

export interface Pillar {
  code: string
  icon: string
  title: string
  desc: string
  artifact: string
}

export const pillars: Pillar[] = [
  {
    code: 'A',
    icon: 'lucide-code-2',
    title: 'landing.pillars.items.kids.title',
    desc: 'landing.pillars.items.kids.desc',
    artifact: 'landing.pillars.items.kids.artifact',
  },
  {
    code: 'B',
    icon: 'lucide-graduation-cap',
    title: 'landing.pillars.items.education.title',
    desc: 'landing.pillars.items.education.desc',
    artifact: 'landing.pillars.items.education.artifact',
  },
  {
    code: 'C',
    icon: 'lucide-chart-no-axes-combined',
    title: 'landing.pillars.items.economy.title',
    desc: 'landing.pillars.items.economy.desc',
    artifact: 'landing.pillars.items.economy.artifact',
  },
]

export interface Partnership {
  icon: string
  tag: string
  title: string
  desc: string
  items: string[]
}

export const partnerships: Partnership[] = [
  {
    icon: 'lucide-landmark',
    tag: 'landing.partnership.grant.tag',
    title: 'landing.partnership.grant.title',
    desc: 'landing.partnership.grant.desc',
    items: [
      'landing.partnership.grant.items.grant',
      'landing.partnership.grant.items.fellow',
      'landing.partnership.grant.items.product',
    ],
  },
  {
    icon: 'lucide-handshake',
    tag: 'landing.partnership.engineering.tag',
    title: 'landing.partnership.engineering.title',
    desc: 'landing.partnership.engineering.desc',
    items: [
      'landing.partnership.engineering.items.beneficiary',
      'landing.partnership.engineering.items.mentoring',
      'landing.partnership.engineering.items.transfer',
    ],
  },
]

export interface Resource {
  icon: string
  title: string
  desc: string
  tag: string
  artifact: string
}

export const resources: Resource[] = [
  {
    icon: 'lucide-chart-no-axes-combined',
    title: 'landing.resources.items.erp.title',
    desc: 'landing.resources.items.erp.desc',
    tag: 'landing.resources.tag',
    artifact: 'landing.resources.items.erp.artifact',
  },
  {
    icon: 'lucide-layout-dashboard',
    title: 'landing.resources.items.cms.title',
    desc: 'landing.resources.items.cms.desc',
    tag: 'landing.resources.tag',
    artifact: 'landing.resources.items.cms.artifact',
  },
]

export interface Contact {
  icon: string
  label: string
  value: string
  href: string
  note?: string
}

export const contacts: Contact[] = [
  {
    icon: 'lucide-mail',
    label: 'landing.contact.email',
    value: 'admiral@nusalargepelago.com',
    href: 'mailto:admiral@nusalargepelago.com',
    note: 'landing.contact.emailNote',
  },
  {
    icon: 'lucide-message-circle',
    label: 'landing.contact.whatsapp',
    value: '+62 819-0794-3762',
    href: 'https://wa.me/6281907943762',
    note: 'landing.contact.whatsappNote',
  },
  {
    icon: 'lucide-map-pin',
    label: 'landing.contact.location',
    value: 'landing.contact.locationValue',
    href: '',
  },
]
