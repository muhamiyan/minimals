import { computed, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  contacts as staticContacts,
  loopSteps as staticLoopSteps,
  partnerships as staticPartnerships,
  pillars as staticPillars,
  resources as staticResources,
} from './content'

interface LandingState {
  pages: Record<string, any>
  items: Record<string, any[]>
  loaded: boolean
}

const state = reactive<LandingState>({ pages: {}, items: {}, loaded: false })

const ICONS: Record<string, Record<string, string>> = {
  loop: {
    research: 'lucide-microscope',
    engineering: 'lucide-code-2',
    outreach: 'lucide-hand-heart',
  },
  pillars: {
    kids: 'lucide-code-2',
    education: 'lucide-graduation-cap',
    economy: 'lucide-chart-no-axes-combined',
  },
  resources: {
    erp: 'lucide-chart-no-axes-combined',
    cms: 'lucide-layout-dashboard',
  },
  partnership: {
    grant: 'lucide-landmark',
    engineering: 'lucide-handshake',
  },
}

const PILLAR_CODES: Record<string, string> = { kids: 'A', education: 'B', economy: 'C' }

function metaOf(entry: any): Record<string, any> {
  return (entry?.meta ?? {}) as Record<string, any>
}

export function useLandingContent() {
  const { t } = useI18n()

  async function ensure(): Promise<void> {}

  const hero = computed(() => {
    const page = state.pages.hero
    const meta = metaOf(page)
    return {
      badge: (meta.badge as string) ?? t('landing.hero.badge'),
      title: page?.title ?? t('landing.hero.title'),
      accent: page?.subtitle ?? t('landing.hero.accent'),
      lead: page?.body ?? t('landing.hero.lead'),
    }
  })

  const loop = computed(() => {
    const page = state.pages.loop
    const meta = metaOf(page)
    const dynamic = state.items.loop ?? []
    const steps = dynamic.length
      ? dynamic.map((item) => ({
          icon: (metaOf(item).icon as string) ?? ICONS.loop[item.key] ?? 'lucide-circle',
          title: item.title,
          desc: item.body ?? '',
        }))
      : staticLoopSteps.map((step) => ({
          icon: step.icon,
          title: t(step.title),
          desc: t(step.desc),
        }))
    return {
      badge: (meta.badge as string) ?? t('landing.loop.badge'),
      title: page?.title ?? t('landing.loop.title'),
      lead: page?.body ?? t('landing.loop.lead'),
      steps,
      return: (meta.return as string) ?? t('landing.loop.return'),
    }
  })

  const pillars = computed(() => {
    const page = state.pages.pillars
    const meta = metaOf(page)
    const dynamic = state.items.pillars ?? []
    const items = dynamic.length
      ? dynamic.map((item) => ({
          code: (metaOf(item).code as string) ?? PILLAR_CODES[item.key] ?? '',
          icon: (metaOf(item).icon as string) ?? ICONS.pillars[item.key] ?? 'lucide-circle',
          title: item.title,
          desc: item.body ?? '',
          artifact: (metaOf(item).artifact as string) ?? '',
        }))
      : staticPillars.map((pillar) => ({
          code: pillar.code,
          icon: pillar.icon,
          title: t(pillar.title),
          desc: t(pillar.desc),
          artifact: t(pillar.artifact),
        }))
    return {
      badge: (meta.badge as string) ?? t('landing.pillars.badge'),
      title: page?.title ?? t('landing.pillars.title'),
      lead: page?.body ?? t('landing.pillars.lead'),
      items,
    }
  })

  const resources = computed(() => {
    const page = state.pages.resources
    const meta = metaOf(page)
    const dynamic = state.items.resources ?? []
    const items = dynamic.length
      ? dynamic.map((item) => ({
          icon: (metaOf(item).icon as string) ?? ICONS.resources[item.key] ?? 'lucide-circle',
          title: item.title,
          desc: item.body ?? '',
          tag: (metaOf(item).tag as string) ?? '',
          artifact: (metaOf(item).artifact as string) ?? '',
        }))
      : staticResources.map((item) => ({
          icon: item.icon,
          title: t(item.title),
          desc: t(item.desc),
          tag: t(item.tag),
          artifact: t(item.artifact),
        }))
    const flagship = (meta.flagship ?? {}) as Record<string, any>
    return {
      badge: (meta.badge as string) ?? t('landing.resources.badge'),
      title: page?.title ?? t('landing.resources.title'),
      lead: page?.body ?? t('landing.resources.lead'),
      tag: (meta.tag as string) ?? t('landing.resources.tag'),
      cta: (meta.cta as string) ?? t('landing.resources.cta'),
      items,
      flagship: {
        status: (flagship.status as string) ?? t('landing.resources.flagship.status'),
        desc: (flagship.desc as string) ?? t('landing.resources.flagship.desc'),
        license: (flagship.license as string) ?? t('landing.resources.flagship.license'),
      },
    }
  })

  const partnership = computed(() => {
    const page = state.pages.partnership
    const meta = metaOf(page)
    const dynamic = state.items.partnership ?? []
    const programs = dynamic.length
      ? dynamic.map((item) => ({
          icon: (metaOf(item).icon as string) ?? ICONS.partnership[item.key] ?? 'lucide-circle',
          tag: (metaOf(item).tag as string) ?? '',
          title: item.title,
          desc: item.body ?? '',
          items: (metaOf(item).items as string[]) ?? [],
        }))
      : staticPartnerships.map((program) => ({
          icon: program.icon,
          tag: t(program.tag),
          title: t(program.title),
          desc: t(program.desc),
          items: program.items.map((key) => t(key)),
        }))
    return {
      badge: (meta.badge as string) ?? t('landing.partnership.badge'),
      title: page?.title ?? t('landing.partnership.title'),
      lead: page?.body ?? t('landing.partnership.lead'),
      programs,
    }
  })

  const contact = computed(() => {
    const page = state.pages.contact
    const meta = metaOf(page)
    const dynamic = Object.keys(meta).length > 0
    const entries = dynamic
      ? [
          {
            icon: 'lucide-mail',
            label: (meta.emailLabel as string) ?? t('landing.contact.email'),
            value: (meta.email as string) ?? '',
            href: (meta.email as string) ? `mailto:${meta.email}` : '',
            note: (meta.emailNote as string) ?? '',
          },
          {
            icon: 'lucide-message-circle',
            label: (meta.whatsappLabel as string) ?? t('landing.contact.whatsapp'),
            value: (meta.whatsapp as string) ?? '',
            href: (meta.whatsapp as string)
              ? `https://wa.me/${(meta.whatsapp as string).replace(/[^0-9]/g, '')}`
              : '',
            note: (meta.whatsappNote as string) ?? '',
          },
          {
            icon: 'lucide-map-pin',
            label: (meta.locationLabel as string) ?? t('landing.contact.location'),
            value: (meta.locationValue as string) ?? '',
            href: '',
            note: '',
          },
        ]
      : staticContacts.map((entry) => ({
          icon: entry.icon,
          label: t(entry.label),
          value: entry.value.startsWith('landing.') ? t(entry.value) : entry.value,
          href: entry.href,
          note: entry.note ? t(entry.note) : '',
        }))
    return {
      badge: (meta.badge as string) ?? t('landing.contact.badge'),
      title: page?.title ?? t('landing.contact.title'),
      lead: page?.body ?? t('landing.contact.lead'),
      entries,
    }
  })

  const cta = computed(() => {
    const page = state.pages.cta
    return {
      title: page?.title ?? t('landing.cta.title'),
      lead: page?.body ?? t('landing.cta.lead'),
    }
  })

  const footer = computed(() => {
    const page = state.pages.footer
    const meta = metaOf(page)
    return {
      githubTagline: (meta.githubTagline as string) ?? t('landing.footer.githubTagline'),
      license: (meta.license as string) ?? t('landing.footer.license'),
    }
  })

  return { ensure, hero, loop, pillars, resources, partnership, contact, cta, footer }
}