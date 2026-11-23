<script setup lang="ts">
import Shimmer from '@/shared/components/Shimmer.vue'
import ShimmerPage from '@/shared/components/ShimmerPage.vue'
import { Button, ErrorMessage, FileUploader, FormControl, dialog, toast } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, articleToolbar } from 'frappe-ui/editor'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { fetchCsrfToken } from '@/shared/api'

import { useActivityStore } from '../store'

const route = useRoute()
const router = useRouter()
const activities = useActivityStore()
const { t } = useI18n()

const isEdit = computed(() => route.name === 'ActivityAdminEdit')
const slug = computed(() => String(route.params.slug || ''))

const form = reactive({
  title: '',
  slug: '',
  body: '',
  status: 'draft',
  coverImage: '',
})
const saving = ref(false)
const deleting = ref(false)

const pageTitle = computed(() =>
  isEdit.value ? t('activity.admin.editActivity') : t('activity.admin.newActivity'),
)
const gateReady = computed(() => !isEdit.value || activities.checked)
const canSave = computed(
  () => Boolean(form.title.trim() && form.body.trim() && !saving.value),
)

onMounted(async () => {
  activities.clearError()
  await fetchCsrfToken().catch(() => '')
  if (isEdit.value) {
    const loaded = await activities.fetchActivity(slug.value)
    if (loaded && activities.activity) {
      form.title = activities.activity.title
      form.slug = activities.activity.slug
      form.body = activities.activity.body
      form.status = activities.activity.status
      form.coverImage = activities.activity.coverImage ?? ''
    }
  }
})

function onEditorChange(value: unknown) {
  if (typeof value === 'string') {
    form.body = value
  }
}

function onCoverUploaded(data: unknown) {
  const url =
    (data as { url?: string }).url ?? (data as { file_url?: string }).file_url
  if (url) {
    form.coverImage = url
  }
}

async function onSave() {
  if (!canSave.value) return
  saving.value = true
  const payload = {
    title: form.title.trim(),
    body: form.body,
    status: form.status,
    coverImage: form.coverImage,
  }
  const saved = isEdit.value
    ? await activities.updateActivity(slug.value, payload)
    : await activities.createActivity({ ...payload, slug: form.slug.trim() || undefined })
  saving.value = false
  if (saved) {
    toast.success(
      t(isEdit.value ? 'activity.admin.toast.updated' : 'activity.admin.toast.created'),
    )
    router.push({ name: 'ActivityAdminList' })
  } else {
    toast.error(activities.error)
  }
}

function onDelete() {
  dialog.danger({
    title: t('activity.admin.confirm.title'),
    message: t('activity.admin.confirm.message'),
    onConfirm: async () => {
      deleting.value = true
      const removed = await activities.removeActivity(slug.value)
      deleting.value = false
      if (removed) {
        toast.success(t('activity.admin.toast.deleted'))
        router.push({ name: 'ActivityAdminList' })
      } else {
        toast.error(activities.error)
      }
    },
  })
}
</script>

<template>
  <ShimmerPage v-if="!gateReady" />
  <div v-else class="mx-auto w-full max-w-3xl p-6">
    <header class="mb-6">
      <h1 class="text-2xl-semibold text-ink-gray-9">{{ pageTitle }}</h1>
      <p v-if="isEdit" class="mt-1 text-p-sm text-ink-gray-5">/{{ slug }}</p>
    </header>

    <ErrorMessage v-if="activities.error && !saving" :message="activities.error" />

    <div v-if="isEdit && activities.loadingActivity" class="space-y-4">
      <Shimmer class="h-10 w-2/3  rounded-4 bg-surface-elevation-2" />
      <Shimmer class="h-10 w-1/3  rounded-4 bg-surface-elevation-2" />
      <Shimmer class="h-72  rounded-6 bg-surface-elevation-2" />
    </div>

    <form v-else class="space-y-5" @submit.prevent="onSave">
      <FormControl
        v-model="form.title"
        :label="t('activity.admin.form.title')"
        :placeholder="t('activity.admin.form.titlePlaceholder')"
        required
      />
      <FormControl
        v-if="!isEdit"
        v-model="form.slug"
        :label="t('activity.admin.form.slug')"
        placeholder="generated-from-title"
        :description="t('activity.admin.form.slugHint')"
      />
      <FormControl
        v-model="form.status"
        type="select"
        :label="t('activity.admin.form.status')"
        :options="[
          { label: t('activity.admin.form.draft'), value: 'draft' },
          { label: t('activity.admin.form.published'), value: 'published' },
        ]"
      />

      <div>
        <div class="mb-1.5 text-base-medium text-ink-gray-7">
          {{ t('activity.admin.form.cover') }}
        </div>
        <FileUploader
          upload-endpoint="/api/v1/uploads"
          :private="false"
          file-types="image/*"
          @success="onCoverUploaded"
        >
          <template #default="{ uploading, progress, error, openFileSelector }">
            <div class="flex flex-wrap items-center gap-3">
              <Button
                type="button"
                :label="t('activity.admin.form.uploadCover')"
                size="sm"
                variant="subtle"
                icon-left="lucide-image-plus"
                :loading="uploading"
                @click="openFileSelector"
              />
              <span v-if="uploading" class="text-p-sm text-ink-gray-5">
                {{ t('activity.admin.form.uploading', { n: progress }) }}
              </span>
              <span v-if="error" class="text-p-sm text-ink-red-6">{{ error }}</span>
            </div>
          </template>
        </FileUploader>
        <div v-if="form.coverImage" class="mt-3 flex items-center gap-3">
          <img
            :src="form.coverImage"
            alt=""
            class="h-16 w-28 rounded-4 border border-outline-gray-1 object-cover"
          />
          <Button
            type="button"
            :label="t('activity.admin.form.remove')"
            size="sm"
            variant="ghost"
            theme="red"
            icon-left="lucide-x"
            @click="form.coverImage = ''"
          />
        </div>
      </div>

      <div>
        <div class="mb-1.5 text-base-medium text-ink-gray-7">
          {{ t('activity.admin.form.body') }}
        </div>
        <div
          class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2 focus-within:border-outline-gray-3"
        >
          <Editor
            :model-value="form.body"
            :extensions="[RichTextKit]"
            format="html"
            :placeholder="t('activity.admin.form.bodyPlaceholder')"
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
          :label="t('activity.admin.actions.delete')"
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
            :label="t('activity.admin.actions.cancel')"
            variant="ghost"
            :route="{ name: 'ActivityAdminList' }"
          />
          <Button
            type="submit"
            :label="t('activity.admin.actions.save')"
            variant="solid"
            theme="green"
            icon-left="lucide-check"
            :loading="saving"
            :disabled="!canSave"
          />
        </div>
      </div>
    </form>
  </div>
</template>
