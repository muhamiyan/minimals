<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Button,
  Dialog,
  ErrorMessage,
  MultiSelect,
  Select,
  Switch,
  TextInput,
  toast,
} from 'frappe-ui'

import { useAccountStore, type AdminUser } from '../store'

const props = defineProps<{
  user: AdminUser | null
}>()

const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{
  saved: []
}>()

const store = useAccountStore()
const { t } = useI18n()

const fullName = ref('')
const appRole = ref('user')
const isActive = ref(true)
const roleNames = ref<string[]>([])
const saving = ref(false)
const error = ref('')

watch(
  () => props.user,
  (user) => {
    fullName.value = user?.fullName ?? ''
    appRole.value = user?.appRole ?? 'user'
    isActive.value = user?.isActive ?? true
    roleNames.value = [...(user?.roles ?? [])]
    error.value = ''
  },
  { immediate: true },
)

onMounted(() => store.fetchRoles())

const appRoleOptions = computed(() => [
  { label: t('account.roleUser'), value: 'user' },
  { label: t('account.roleAdmin'), value: 'admin' },
])

const roleOptions = computed(() =>
  store.roles.map((role) => ({ label: role.name, value: role.name })),
)

const actions = computed(() => [
  {
    label: t('shared.cancel'),
    variant: 'ghost' as const,
    theme: 'gray' as const,
    onClick: ({ close }: { close: () => void }) => close(),
  },
  {
    label: t('account.saveChanges'),
    variant: 'solid' as const,
    loading: saving.value,
    onClick: async () => {
      await onSave()
    },
  },
])

async function onSave() {
  if (!props.user) return
  saving.value = true
  error.value = ''
  const updated = await store.updateUser(props.user.id, {
    fullName: fullName.value.trim(),
    appRole: appRole.value,
    isActive: isActive.value,
    roleNames: [...roleNames.value],
  })
  saving.value = false
  if (!updated) {
    error.value = store.error
    return
  }
  toast.success(t('account.userUpdated'))
  open.value = false
  emit('saved')
}
</script>

<template>
  <Dialog v-model:open="open" :title="t('account.editUser')" icon="lucide-user-pen" :actions="actions">
    <div class="space-y-4">
      <ErrorMessage v-if="error" :message="error" />

      <TextInput
        v-model="fullName"
        :label="t('account.fullName')"
        required
      />

      <Select
        v-model="appRole"
        :label="t('account.appRole')"
        :options="appRoleOptions"
      />

      <MultiSelect
        v-model="roleNames"
        :label="t('account.roleNames')"
        :options="roleOptions"
        :placeholder="t('account.rolesPlaceholder')"
      />

      <Switch v-model="isActive" :label="t('account.isActive')" />
    </div>
  </Dialog>
</template>
