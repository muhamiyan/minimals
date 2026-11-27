<script setup lang="ts">
import { Button, Combobox, ErrorMessage, FormControl, dialog, toast, Spinner } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu, RichTextKit, articleToolbar } from 'frappe-ui/editor'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import CoverImageField from '@/shared/components/CoverImageField.vue'

import { fetchCsrfToken } from '@/shared/api'
import AppPageHeader from '@/shared/shell/AppPageHeader.vue'

import { useBlogStore } from '../store'

const route = useRoute()
const router = useRouter()
const blog = useBlogStore()
const { t } = useI18n()

const isEdit = computed(() => route.name === 'BlogAdminEdit')
const slug = computed(() => String(route.params.slug || ''))

const form = reactive({
  title: '',
  slug: '',
  body: '',
  status: 'draft',
  coverImage: '',
  author: '',
  category: '',
})
const saving = ref(false)
const deleting = ref(false)

const gateReady = computed(() => !isEdit.value || blog.checked)
const pageTitle = computed(() =>
  isEdit.value ? t('blog.admin.editPost') : t('blog.admin.newPost'),
)
const canSave = computed(
  () => Boolean(form.title.trim() && form.body.trim() && !saving.value),
)

const categoryOptions = computed(() => [
  ...blog.categories.map((category) => ({
    label: category.name,
    value: category.name,
  })),
  {
    type: 'custom' as const,
    key: 'new-category',
    label: t('blog.admin.form.createCategory'),
    icon: 'lucide-plus',
    onClick: ({ query }: { query: string }) => openCreateCategory(query),
  },
])

function onCategoryChange(value: unknown) {
  form.category = typeof value === 'string' ? value : ''
}

function openCreateCategory(query = '') {
  dialog.prompt({
    title: t('blog.admin.form.createCategory'),
    fields: [
      {
        name: 'name',
        label: t('blog.admin.form.category'),
        placeholder: t('blog.admin.form.categoryPlaceholder'),
        defaultValue: query,
        required: true,
      },
    ],
    confirmLabel: t('blog.admin.form.createCategory'),
    onConfirm: async ({ values }) => {
      const name = String(values.name ?? '').trim()
      if (!name) return

      const existing = blog.categories.find(
        (category) => category.name.toLowerCase() === name.toLowerCase(),
      )
      if (existing) {
        form.category = existing.name
        return
      }

      const created = await blog.createCategory(name)
      if (!created) throw new Error(blog.categoryError)
      form.category = created.name
      toast.success(t('blog.admin.toast.categoryCreated'))
    },
  })
}

onMounted(async () => {
  blog.clearError()
  await fetchCsrfToken().catch(() => '')
  await blog.fetchCategories()
  if (isEdit.value) {
    const loaded = await blog.fetchPost(slug.value)
    if (loaded && blog.post) {
      form.title = blog.post.title
      form.slug = blog.post.slug
      form.body = blog.post.body
      form.status = blog.post.status
      form.coverImage = blog.post.coverImage ?? ''
      form.author = blog.post.author ?? ''
      form.category = blog.post.category ?? ''
    }
  }
})

function onEditorChange(value: unknown) {
  if (typeof value === 'string') {
    form.body = value
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
    author: form.author.trim(),
    category: form.category.trim(),
  }
  const saved = isEdit.value
    ? await blog.updatePost(slug.value, payload)
    : await blog.createPost({ ...payload, slug: form.slug.trim() || undefined })
  saving.value = false
  if (saved) {
    toast.success(t(isEdit.value ? 'blog.admin.toast.updated' : 'blog.admin.toast.created'))
    router.push({ name: 'BlogAdminList' })
  } else {
    toast.error(blog.error)
  }
}

function onDelete() {
  dialog.danger({
    title: t('blog.admin.confirm.title'),
    message: t('blog.admin.confirm.message'),
    onConfirm: async () => {
      deleting.value = true
      const removed = await blog.removePost(slug.value)
      deleting.value = false
      if (removed) {
        toast.success(t('blog.admin.toast.deleted'))
        router.push({ name: 'BlogAdminList' })
      } else {
        toast.error(blog.error)
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

    <ErrorMessage v-if="blog.error && !saving" :message="blog.error" />

    <div v-if="isEdit && blog.loadingPost" class="space-y-4">
      <div class="h-10 w-2/3 rounded-4 animate-pulse bg-surface-elevation-2" />
      <div class="h-10 w-1/3 rounded-4 animate-pulse bg-surface-elevation-2" />
      <div class="h-72 rounded-6 animate-pulse bg-surface-elevation-2" />
    </div>

    <form v-else class="space-y-5" @submit.prevent="onSave">
      <FormControl
        v-model="form.title"
        :label="t('blog.admin.form.title')"
        :placeholder="t('blog.admin.form.titlePlaceholder')"
        required
      />
      <FormControl
        v-if="!isEdit"
        v-model="form.slug"
        :label="t('blog.admin.form.slug')"
        placeholder="generated-from-title"
        :description="t('blog.admin.form.slugHint')"
      />
      <FormControl
        v-model="form.author"
        :label="t('blog.admin.form.author')"
        :placeholder="t('blog.admin.form.authorPlaceholder')"
      />
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Combobox
          :model-value="form.category || null"
          :options="categoryOptions"
          :label="t('blog.admin.form.category')"
          :placeholder="t('blog.admin.form.categoryPlaceholder')"
          :empty-text="t('blog.admin.form.noCategories')"
          @update:model-value="onCategoryChange"
        />
        <FormControl
          v-model="form.status"
          type="select"
          :label="t('blog.admin.form.status')"
          :options="[
            { label: t('blog.admin.form.draft'), value: 'draft' },
            { label: t('blog.admin.form.published'), value: 'published' },
          ]"
        />
      </div>

      <CoverImageField
        v-model="form.coverImage"
        label-key="blog.admin.form.cover"
        upload-label-key="blog.admin.form.uploadCover"
        remove-label-key="blog.admin.form.remove"
        uploading-label-key="blog.admin.form.uploading"
      />

      <div>
        <div class="mb-1.5 text-base-medium text-ink-gray-7">
          {{ t('blog.admin.form.body') }}
        </div>
        <div
          class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2 focus-within:border-outline-gray-3"
        >
          <Editor
            :model-value="form.body"
            :extensions="[RichTextKit]"
            format="html"
            :placeholder="t('blog.admin.form.bodyPlaceholder')"
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

      <div class="flex flex-wrap items-center justify-between gap-2 border-t border-outline-gray-1 pt-4">
        <Button
          v-if="isEdit"
          type="button"
          :label="t('blog.admin.actions.delete')"
          variant="subtle"
          theme="red"
          icon-left="lucide-trash-2"
          :loading="deleting"
          @click="onDelete"
        />
        <div class="ml-auto flex items-center gap-2">
          <Button
            type="button"
            :label="t('blog.admin.actions.cancel')"
            variant="ghost"
            theme="gray"
            :route="{ name: 'BlogAdminList' }"
          />
          <Button
            type="submit"
            :label="t('blog.admin.actions.save')"
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
