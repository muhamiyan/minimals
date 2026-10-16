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
    title: 'Layered domains',
    desc: 'Seven files per domain, dependencies pointing only downward. A bug has exactly one address.',
  },
  {
    icon: 'lucide-key-round',
    title: 'Session & API-key auth',
    desc: 'Browser sessions via Flask-Login; services authenticate with bcrypt-hashed API keys behind a 10-char lookup prefix.',
  },
  {
    icon: 'lucide-shield-check',
    title: 'Security defaults',
    desc: 'CSRF on every write, per-IP rate limits, CSP + HSTS, and forwarded headers believed only from private peers.',
  },
  {
    icon: 'lucide-users',
    title: 'Roles & RBAC',
    desc: 'A hard-coded app role for real checks, relational roles for labels, and require_role helpers that return.',
  },
  {
    icon: 'lucide-rocket',
    title: 'First-run setup',
    desc: 'SQLite, MariaDB or PostgreSQL: test, migrate, create the admin — the engine hot-swaps, loopback-only.',
  },
  {
    icon: 'lucide-heart-pulse',
    title: 'Health & audit',
    desc: '/health and /ready probes, rotating logs, an audit trail per write, and alerts that never break the business flow.',
  },
  {
    icon: 'lucide-panels-top-left',
    title: 'Vue 3 SPA included',
    desc: 'frappe-ui on Tailwind tokens, built straight into Flask’s static folder. One process, one origin, one deploy.',
  },
  {
    icon: 'lucide-git-branch',
    title: 'Migrations on boot',
    desc: 'Flip MIGRATE_ON_BOOT and Alembic runs before the server accepts traffic — schema and models stay in step across engines.',
  },
]

export const principles = [
  'Dependencies point only downward — api, dto, services, repositories, models, presenters.',
  'Services own the transaction; repositories never commit.',
  'Bare objects on success, a single snake_case key on failure.',
  'Raise exceptions from services — never return responses.',
  'Fix at the point of failure. No history to dig through.',
]
