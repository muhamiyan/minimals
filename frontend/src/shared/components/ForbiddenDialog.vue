<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Dialog, type DialogAction } from 'frappe-ui'

const props = withDefaults(
  defineProps<{
    title?: string
    message?: string
    redirectTo?: string
  }>(),
  {
    redirectTo: '/',
  },
)

const router = useRouter()
const { t } = useI18n()
const open = ref(false)

const resolvedTitle = computed(() => props.title || t('shared.forbiddenTitle'))
const resolvedMessage = computed(() => props.message || t('shared.forbiddenMessage'))

let pendingTimer: ReturnType<typeof setTimeout> | null = null
let shownAt = 0

function onForbidden() {
  if (open.value || Date.now() - shownAt < 1000) return
  if (pendingTimer) clearTimeout(pendingTimer)
  pendingTimer = setTimeout(() => {
    open.value = true
    shownAt = Date.now()
  }, 150)
}

function close() {
  open.value = false
  shownAt = 0
  router.replace(props.redirectTo)
}

onMounted(() => {
  window.addEventListener('api:forbidden', onForbidden)
})

onBeforeUnmount(() => {
  window.removeEventListener('api:forbidden', onForbidden)
  if (pendingTimer) clearTimeout(pendingTimer)
})

const actions = computed<DialogAction[]>(() => [
  { label: t('shared.ok'), variant: 'solid', onClick: close },
])
</script>

<template>
  <Dialog
    :open="open"
    :title="resolvedTitle"
    :message="resolvedMessage"
    icon="lucide-shield-x"
    theme="red"
    :actions="actions"
    @update:open="close"
  />
</template>
