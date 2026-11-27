<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Button, ErrorMessage, FormControl, Spinner, toast } from 'frappe-ui'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import { siteContent } from '@/shared/siteContent'
import { sectionByKey, SITE_SECTIONS } from '../sections'
import RichTextField from '../components/RichTextField.vue'
import {
  MAPS_EMBED_URL,
  PPDB_URL,
  contact as defaultContact,
} from '@/features/landing/content'
import { useSiteContentStore } from '../store'

type FieldKind = 'text' | 'textarea' | 'editor' | 'literal'
type FieldDef = {
  path: string
  labelKey: string
  kind: FieldKind
  fallbackText?: string
  fallbackValue?: string
}
type SectionDef = { key: string; fields: FieldDef[] }

const route = useRoute()
const { t } = useI18n()
const store = useSiteContentStore()
const form = reactive<Record<string, any>>({})
const gateReady = ref(false)

const activeKey = computed(
  () => SITE_SECTIONS.find((item) => item.routeName === route.name)?.key ?? SITE_SECTIONS[0].key,
)
const activeDef = computed(() => sectionByKey(activeKey.value))
const activeSectionKeys = computed(() => activeDef.value?.sectionKeys ?? [])

const text = (
  path: string,
  labelKey: string,
  fallbackText: string,
  kind: FieldKind = 'text',
): FieldDef => ({ path, labelKey, kind, fallbackText })

const literal = (path: string, labelKey: string, fallbackValue: string): FieldDef =>
  ({ path, labelKey, kind: 'literal', fallbackValue })

const sections: SectionDef[] = [
  {
    key: 'ppdb',
    fields: [
      literal('ppdb.url', 'siteContent.admin.fields.url', PPDB_URL),
      text('ppdb.title', 'siteContent.admin.fields.title', 'landing.ppdb.title'),
      text('ppdb.lead', 'siteContent.admin.fields.lead', 'landing.ppdb.lead', 'editor'),
      text('ppdb.period', 'siteContent.admin.fields.period', 'landing.ppdb.period', 'literal'),
      text('ppdb.hours', 'siteContent.admin.fields.hours', 'landing.hero.hours', 'literal'),
      text('ppdb.location', 'siteContent.admin.fields.location', 'landing.hero.location', 'literal'),
    ],
  },
  {
    key: 'contact',
    fields: [
      literal('contact.studentCount', 'siteContent.admin.fields.studentCount', '3+'),
      literal('contact.staffCount', 'siteContent.admin.fields.staffCount', '100+'),
      literal('contact.address', 'siteContent.admin.fields.address', defaultContact.address),
      literal('contact.email', 'siteContent.admin.fields.email', defaultContact.email),
      literal('contact.whatsappUrl', 'siteContent.admin.fields.whatsappUrl', defaultContact.whatsapp),
      literal('contact.whatsappDisplay', 'siteContent.admin.fields.whatsappDisplay', '0878 6470 6565'),
      literal('contact.facebookUrl', 'siteContent.admin.fields.facebookUrl', defaultContact.facebook),
      literal('contact.facebookDisplay', 'siteContent.admin.fields.facebookDisplay', 'manw.selaparangkediri'),
      literal('contact.mapsUrl', 'siteContent.admin.fields.mapsUrl', MAPS_EMBED_URL),
    ],
  },
]

const visibleSections = computed(() =>
  sections.filter((section) => activeSectionKeys.value.includes(section.key)),
)

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function getField(path: string): any {
  return path.split('.').reduce<any>((node, part) => node?.[part], form)
}

function displayValue(field: FieldDef): string {
  const value = getField(field.path)
  if (typeof value === 'string' && value.trim()) return value
  if (field.fallbackValue) return field.fallbackValue
  return field.fallbackText ? t(field.fallbackText) : ''
}

function setField(path: string, value: unknown): void {
  const parts = path.split('.')
  const last = parts.pop()
  const parent = parts.reduce<any>((node, part) => node?.[part], form)
  if (parent && last) parent[last] = value
}

function payload(): Partial<Record<string, unknown>> {
  const result: Record<string, unknown> = {
    configuredSections: [
      ...new Set([...(form.configuredSections ?? []), ...activeSectionKeys.value]),
    ],
  }
  for (const key of activeSectionKeys.value) result[key] = clone(form[key])
  return result
}

async function save(): Promise<void> {
  const saved = await store.saveContent(payload() as any)
  if (saved) {
    Object.assign(form, clone(saved))
    toast.success(t('siteContent.admin.saved'))
  }
}

onMounted(async () => {
  const data = await store.fetchContent()
  Object.assign(form, clone(data ?? siteContent))
  gateReady.value = true
})

</script>

<template>
  <AppPageHeader />

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-2xl px-5 py-6">
    <p class="mb-6 text-p-sm text-ink-gray-5">{{ t('siteContent.admin.lead') }}</p>

    <ErrorMessage v-if="store.error" :message="store.error" />

    <form class="space-y-6" @submit.prevent="save">
      <div
        v-for="section in visibleSections"
        :key="section.key"
        class="space-y-4"
      >
        <div class="grid gap-4 md:grid-cols-2">
          <template v-for="field in section.fields" :key="field.path">
            <div v-if="field.kind === 'editor'" class="md:col-span-2">
              <div class="mb-1.5 text-base-medium text-ink-gray-7">
                {{ t(field.labelKey) }}
              </div>
              <RichTextField
                :model-value="displayValue(field)"
                @update:model-value="setField(field.path, $event)"
              />
            </div>
            <FormControl
              v-else
              :label="t(field.labelKey)"
              :type="field.kind === 'textarea' ? 'textarea' : 'text'"
              :model-value="displayValue(field)"
              @update:model-value="setField(field.path, $event)"
            />
          </template>
        </div>
      </div>

      <div class="flex justify-end gap-3">
        <Button
          type="submit"
          variant="solid"
          theme="gray"
          icon-left="lucide-check"
          :label="t('siteContent.admin.save')"
          :loading="store.saving"
        />
      </div>
    </form>
  </div>
</template>
