export const stack = [
  'Flask',
  'Vue 3',
  'SQLAlchemy',
  'Alembic',
  'frappe-ui',
  'Tailwind',
  'waitress',
  'Caddy',
]

export const pipeline = [
  'api',
  'dto',
  'services',
  'repositories',
  'models',
  'presenters',
]

export interface Feature {
  icon: string
  title: string
  desc: string
}

export const features: Feature[] = [
  {
    icon: 'lucide-layers-3',
    title: 'landing.features.items.layered.title',
    desc: 'landing.features.items.layered.desc',
  },
  {
    icon: 'lucide-key-round',
    title: 'landing.features.items.auth.title',
    desc: 'landing.features.items.auth.desc',
  },
  {
    icon: 'lucide-shield-check',
    title: 'landing.features.items.security.title',
    desc: 'landing.features.items.security.desc',
  },
  {
    icon: 'lucide-users',
    title: 'landing.features.items.roles.title',
    desc: 'landing.features.items.roles.desc',
  },
  {
    icon: 'lucide-rocket',
    title: 'landing.features.items.setup.title',
    desc: 'landing.features.items.setup.desc',
  },
  {
    icon: 'lucide-heart-pulse',
    title: 'landing.features.items.health.title',
    desc: 'landing.features.items.health.desc',
  },
  {
    icon: 'lucide-panels-top-left',
    title: 'landing.features.items.spa.title',
    desc: 'landing.features.items.spa.desc',
  },
  {
    icon: 'lucide-git-branch',
    title: 'landing.features.items.migrations.title',
    desc: 'landing.features.items.migrations.desc',
  },
]

export const principles = [
  'landing.about.principles.p1',
  'landing.about.principles.p2',
  'landing.about.principles.p3',
  'landing.about.principles.p4',
  'landing.about.principles.p5',
]
