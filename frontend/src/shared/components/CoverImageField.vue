<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Dialog, ErrorMessage, FileUploader } from 'frappe-ui'

import { api, getErrorMessage } from '@/shared/api'

import ImageCropper from './ImageCropper.vue'

const model = defineModel<string>('modelValue', { default: '' })

const props = withDefaults(
  defineProps<{
    labelKey: string
    uploadLabelKey: string
    removeLabelKey: string
    uploadingLabelKey: string
    aspect?: number
  }>(),
  { aspect: 16 / 9 },
)

const { t } = useI18n()
const pending = ref<File | null>(null)
const cropOpen = ref(false)
const previousUrl = ref('')
const uploading = ref(false)
const error = ref('')

async function cropExisting() {
  if (!model.value) return
  previousUrl.value = model.value
  error.value = ''
  try {
    const response = await fetch(model.value)
    if (!response.ok) throw new Error('load_failed')
    const blob = await response.blob()
    pending.value = new File(
      [blob],
      'cover.png',
      { type: blob.type || 'image/png' },
    )
    cropOpen.value = true
  } catch {
    error.value = t('shared.crop.loadFailed')
  }
}

function onUploaded(upload: any) {
  const url =
    typeof upload?.url === 'string'
      ? upload.url
      : typeof upload?.file_url === 'string'
        ? upload.file_url
        : ''
  if (url) model.value = url
}

function onCancel() {
  cropOpen.value = false
  pending.value = null
}

function undoCrop() {
  if (!previousUrl.value) return
  model.value = previousUrl.value
  previousUrl.value = ''
  error.value = ''
}

function onCropError() {
  error.value = t('shared.crop.loadFailed')
}

async function onApply(blob: Blob) {
  error.value = ''
  uploading.value = true
  try {
    const body = new FormData()
    body.append('file', new File([blob], 'cover.png', { type: 'image/png' }))
    const { data } = await api.post('/uploads', body)
    const url = typeof data?.url === 'string' ? data.url : ''
    if (!url) throw new Error('upload_failed')
    model.value = url
    cropOpen.value = false
    pending.value = null
  } catch (e: any) {
    error.value = getErrorMessage(e, t('shared.crop.uploadFailed'))
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div>
    <div class="mb-1.5 text-base-medium text-ink-gray-7">
      {{ t(props.labelKey) }}
    </div>

    <FileUploader
      upload-endpoint="/api/v1/uploads"
      :private="false"
      file-types="image/*"
      @success="onUploaded"
    >
      <template #default="{ uploading: fileUploading, progress, error: uploadError, openFileSelector }">
        <div class="mt-3 flex flex-wrap items-center gap-3">
          <img
            v-if="model"
            :src="model"
            alt=""
            class="h-16 w-28 rounded-4 border border-outline-gray-1 object-cover"
          />
          <Button
            type="button"
            :label="t(props.uploadLabelKey)"
            size="sm"
            variant="subtle"
            icon-left="lucide-image-plus"
            :loading="fileUploading"
            @click="openFileSelector"
          />
          <Button
            v-if="model"
            type="button"
            :label="t('shared.crop.edit')"
            size="sm"
            variant="subtle"
            theme="gray"
            icon-left="lucide-pencil"
            @click="cropExisting"
          />
          <Button
            v-if="previousUrl && model !== previousUrl"
            type="button"
            :label="t('shared.crop.undo')"
            size="sm"
            variant="subtle"
            theme="gray"
            icon-left="lucide-rotate-ccw"
            @click="undoCrop"
          />
          <Button
            v-if="model"
            type="button"
            :label="t(props.removeLabelKey)"
            size="sm"
            variant="ghost"
            theme="red"
            icon-left="lucide-x"
            @click="model = ''"
          />
          <span v-if="fileUploading" class="text-p-sm text-ink-gray-5">
            {{ t(props.uploadingLabelKey, { n: progress }) }}
          </span>
          <span v-if="uploadError" class="text-p-sm text-ink-red-6">{{ uploadError }}</span>
        </div>
      </template>
    </FileUploader>

    <ErrorMessage v-if="error" :message="error" class="mt-2" />

    <Dialog
      v-model:open="cropOpen"
      :title="t('shared.crop.title')"
      :actions="[]"
    >
      <ImageCropper
        v-if="pending"
        :file="pending"
        :busy="uploading"
        :aspect="props.aspect"
        hide-title
        @cancel="onCancel"
        @apply="onApply"
        @error="onCropError"
      />
    </Dialog>
  </div>
</template>
