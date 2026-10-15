<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Dialog, type DialogAction } from 'frappe-ui'

const props = withDefaults(
  defineProps<{
    title?: string
    message?: string
    redirectTo?: string
  }>(),
  {
    title: 'Access denied',
    message:
      'This page requires administrator privileges. Your account is registered as a regular user. Contact an administrator to get access.',
    redirectTo: '/',
  },
)

const router = useRouter()
const open = ref(false)

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

const actions: DialogAction[] = [
  { label: 'OK', variant: 'solid', onClick: close },
]
</script>

<template>
  <Dialog
    :open="open"
    :title="title"
    :message="message"
    icon="lucide-shield-x"
    theme="red"
    :actions="actions"
    @update:open="close"
  />
</template>
