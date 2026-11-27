export const PPDB_URL = 'https://forms.gle/b979B8YdGVm1Me2t7'

export const MAPS_EMBED_URL =
  'https://www.google.com/maps?q=-8.636914%2C116.154089&z=16&hl=id&gl=ID&output=embed'

export const MAPS_LINK_URL =
  'https://www.google.com/maps?ll=-8.636914,116.154089&z=16&t=m&hl=id&gl=ID&mapclient=embed&cid=6457943705581396349'

export const contact = {
  address: 'Jl. TGH Abdul Hafidz, Kediri, Lombok Barat, Nusa Tenggara Barat',
  email: 'siimad.ponpesselaparang@gmail.com',
  whatsapp: 'https://wa.me/087864706565',
  facebook: 'https://www.facebook.com/manw.selaparangkediri',
}

export interface Highlight {
  icon: string
  title: string
  desc: string
}

export const highlights: Highlight[] = [
  {
    icon: 'lucide-school',
    title: 'landing.highlights.items.management.title',
    desc: 'landing.highlights.items.management.desc',
  },
  {
    icon: 'lucide-book-open',
    title: 'landing.highlights.items.curriculum.title',
    desc: 'landing.highlights.items.curriculum.desc',
  },
  {
    icon: 'lucide-shield-check',
    title: 'landing.highlights.items.accreditation.title',
    desc: 'landing.highlights.items.accreditation.desc',
  },
  {
    icon: 'lucide-users',
    title: 'landing.highlights.items.teachers.title',
    desc: 'landing.highlights.items.teachers.desc',
  },
  {
    icon: 'lucide-wrench',
    title: 'landing.highlights.items.facilities.title',
    desc: 'landing.highlights.items.facilities.desc',
  },
  {
    icon: 'lucide-handshake',
    title: 'landing.highlights.items.network.title',
    desc: 'landing.highlights.items.network.desc',
  },
  {
    icon: 'lucide-gift',
    title: 'landing.highlights.items.scholarship.title',
    desc: 'landing.highlights.items.scholarship.desc',
  },
  {
    icon: 'lucide-graduation-cap',
    title: 'landing.highlights.items.integrated.title',
    desc: 'landing.highlights.items.integrated.desc',
  },
]

export interface Stat {
  icon: string
  value: string
  label: string
}

export const stats: Stat[] = [
  {
    icon: 'lucide-graduation-cap',
    value: '7+',
    label: 'landing.stats.programs',
  },
  {
    icon: 'lucide-users',
    value: '3+',
    label: 'landing.stats.students',
  },
  {
    icon: 'lucide-user-check',
    value: '100+',
    label: 'landing.stats.teachers',
  },
  {
    icon: 'lucide-heart',
    value: '0',
    label: 'landing.stats.scholarships',
  },
]

export interface Facility {
  icon: string
  title: string
  desc: string
}

export const facilities: Facility[] = [
  {
    icon: 'lucide-book-open',
    title: 'landing.facilities.items.library.title',
    desc: 'landing.facilities.items.library.desc',
  },
  {
    icon: 'lucide-house',
    title: 'landing.facilities.items.maleDorm.title',
    desc: 'landing.facilities.items.maleDorm.desc',
  },
  {
    icon: 'lucide-users',
    title: 'landing.facilities.items.femaleDorm.title',
    desc: 'landing.facilities.items.femaleDorm.desc',
  },
]

export const principles = [
  'landing.about.principles.p1',
  'landing.about.principles.p2',
  'landing.about.principles.p3',
  'landing.about.principles.p4',
  'landing.about.principles.p5',
]

const assetBase = import.meta.env.BASE_URL

export const heroSlides = [
  `${assetBase}hero/hero-1.jpg`,
  `${assetBase}hero/hero-2.jpg`,
  `${assetBase}hero/hero-3.jpg`,
]

