<script setup lang="ts">
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  RichTextKit,
  articleToolbar,
} from 'frappe-ui/editor'

const model = defineModel<string>({ default: '' })

function onChange(value: unknown) {
  if (typeof value === 'string') model.value = value
}
</script>

<template>
  <div
    class="overflow-hidden rounded-6 border border-outline-gray-1 bg-surface-elevation-2 focus-within:border-outline-gray-3"
  >
    <Editor
      :model-value="model"
      :extensions="[RichTextKit]"
      format="html"
      @change="onChange"
    >
      <template #default>
        <div class="border-b border-outline-gray-1 px-2 py-1.5">
          <EditorFixedMenu :items="articleToolbar" size="sm" />
        </div>
        <EditorContent class="min-h-48 px-4 py-3" />
      </template>
    </Editor>
  </div>
</template>
