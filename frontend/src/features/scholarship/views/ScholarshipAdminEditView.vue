<script setup lang="ts">
import { Button, ErrorMessage, FormControl, dialog, toast, Spinner } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, articleToolbar } from 'frappe-ui/editor'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import CoverImageField from '@/shared/components/CoverImageField.vue'

import { fetchCsrfToken } from '@/shared/api'
import AppPageHeader from '@/shared/shell/AppPageHeader.vue'

import { useScholarshipStore } from '../store'

const route = useRoute()
const router = useRouter()
const scholarships = useScholarshipStore()
const { t } = useI18n()

const isEdit = computed(() => route.name === 'ScholarshipAdminEdit')
const slug = computed(() => String(route.params.slug || ''))

const form = reactive({
  title: '',
  slug: '',
  level: '',
  body: '',
  status: 'draft',
  coverImage: '',
  order: 0,
})
const saving = ref(false)
const deleting = ref(false)

const pageTitle = computed(() =>
  isEdit.value ? t('scholarship.admin.editScholarship') : t('scholarship.admin.newScholarship'),
)
const gateReady = computed(() => !isEdit.value || scholarships.checked)
const canSave = computed(
  () => Boolean(form.title.trim() && form.body.trim() && !saving.value),
)

onMounted(async () => {
  scholarships.clearError()
  await fetchCsrfToken().catch(() => '')
  if (isEdit.value) {
    const loaded = await scholarships.fetchScholarship(slug.value)
    if (loaded && scholarships.scholarship) {
      form.title = scholarships.scholarship.title
      form.slug = scholarships.scholarship.slug
      form.level = scholarships.scholarship.level
      form.body = scholarships.scholarship.body
      form.status = scholarships.scholarship.status
      form.coverImage = scholarships.scholarship.coverImage ?? ''
      form.order = scholarships.scholarship.order
    }
  }
})

function onEditorChange(value: unknown) {
  if (typeof value === 'string') form.body = value
}

async function onSave() {
  if (!canSave.value) return
  saving.value = true
  const payload = {
    title: form.title.trim(),
    level: form.level.trim(),
    body: form.body,
    status: form.status,
    coverImage: form.coverImage,
    order: form.order,
  }
  const saved = isEdit.value
    ? await scholarships.updateScholarship(slug.value, payload)
    : await scholarships.createScholarship({ ...payload, slug: form.slug.trim() || undefined })
  saving.value = false
  if (saved) {
    toast.success(
      t(isEdit.value ? 'scholarship.admin.toast.updated' : 'scholarship.admin.toast.created'),
    )
    router.push({ name: 'ScholarshipAdminList' })
  } else {
    toast.error(scholarships.error)
  }
}

function onDelete() {
  dialog.danger({
    title: t('scholarship.admin.confirm.title'),
    message: t('scholarship.admin.confirm.message'),
    onConfirm: async () => {
      deleting.value = true
      const removed = await scholarships.removeScholarship(slug.value)
      deleting.value = false
      if (removed) {
        toast.success(t('scholarship.admin.toast.deleted'))
        router.push({ name: 'ScholarshipAdminList' })
      } else {
        toast.error(scholarships.error)
      }
    },
  })
}
</script>

<template>
  <AppPageHeader />

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>
  <div v-else class="mx-auto w-full max-w-2xl px-5 py-6">
    <p v-if="isEdit" class="mb-6 text-p-sm text-ink-gray-5">/{{ slug }}</p>

    <ErrorMessage v-if="scholarships.error && !saving" :message="scholarships.error" />

    <div v-if="isEdit && scholarships.loadingScholarship" class="space-y-4">
      <div class="h-10 w-2/3 rounded-4 bg-surface-elevation-2 animate-pulse" />
      <div class="h-10 w-1/3 rounded-4 bg-surface-elevation-2 animate-pulse" />
      <div class="h-72 rounded-6 bg-surface-elevation-2 animate-pulse" />
    </div>

    <form v-else class="space-y-5" @submit.prevent="onSave">
      <FormControl
        v-model="form.title"
        :label="t('scholarship.admin.form.title')"
        :placeholder="t('scholarship.admin.form.titlePlaceholder')"
        required
      />
      <FormControl
        v-if="!isEdit"
        v-model="form.slug"
        :label="t('scholarship.admin.form.slug')"
        placeholder="generated-from-title"
        :description="t('scholarship.admin.form.slugHint')"
      />
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl
          v-model="form.level"
          :label="t('scholarship.admin.form.level')"
          :placeholder="t('scholarship.admin.form.levelPlaceholder')"
        />
        <FormControl
          v-model.number="form.order"
          type="number"
          :label="t('scholarship.admin.form.order')"
        />
      </div>
      <FormControl
        v-model="form.status"
        type="select"
        :label="t('scholarship.admin.form.status')"
        :options="[
          { label: t('scholarship.admin.form.draft'), value: 'draft' },
          { label: t('scholarship.admin.form.published'), value: 'published' },
        ]"
      />

      <CoverImageField
        v-model="form.coverImage"
        label-key="scholarship.admin.form.cover"
        upload-label-key="scholarship.admin.form.uploadCover"
        remove-label-key="scholarship.admin.form.remove"
        uploading-label-key="scholarship.admin.form.uploading"
      />

      <div>
        <div class="mb-1.5 text-base-medium text-ink-gray-7">
          {{ t('scholarship.admin.form.body') }}
        </div>
        <div
          class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2 focus-within:border-outline-gray-3"
        >
          <Editor
            :model-value="form.body"
            :extensions="[RichTextKit]"
            format="html"
            :placeholder="t('scholarship.admin.form.bodyPlaceholder')"
            @change="onEditorChange"
          >
            <template #default>
              <div class="border-b border-outline-gray-1 px-2 py-1.5">
                <EditorFixedMenu :items="articleToolbar" size="sm" />
              </div>
              <EditorContent class="min-h-72 px-4 py-3" />
            </template>
          </Editor>
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 pt-2">
        <Button
          v-if="isEdit"
          type="button"
          :label="t('scholarship.admin.actions.delete')"
          variant="subtle"
          theme="red"
          icon-left="lucide-trash-2"
          :loading="deleting"
          @click="onDelete"
        />
        <span v-else />
        <div class="flex items-center gap-2">
          <Button
            type="button"
            :label="t('scholarship.admin.actions.cancel')"
            variant="ghost"
            :route="{ name: 'ScholarshipAdminList' }"
          />
          <Button
            type="submit"
            :label="t('scholarship.admin.actions.save')"
            variant="solid"
            theme="gray"
            icon-left="lucide-check"
            :loading="saving"
            :disabled="!canSave"
          />
        </div>
      </div>
    </form>
  </div>
</template>
