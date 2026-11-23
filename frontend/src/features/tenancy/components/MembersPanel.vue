<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Dialog, ErrorMessage, FormControl, Select, Spinner, dialog, toast } from 'frappe-ui'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import ListHead from '@/shared/components/ListHead.vue'
import { LIST_ROW_SURFACE_CLASS } from '@/shared/listRow'

import { MEMBER_ROLES, roleLabel, useTenancyStore } from '../store'

const props = defineProps<{ orgId: string; canManage?: boolean }>()

const { t } = useI18n()
const memberColumns = computed(() =>
  props.canManage
    ? ['minmax(0,1fr)', '90px', '36px']
    : ['minmax(0,1fr)', '90px'],
)
const roleOptions = computed(() =>
  MEMBER_ROLES.map((role) => ({ label: roleLabel(role), value: role })),
)

const store = useTenancyStore()

const memberDialogOpen = ref(false)
const memberIdentifier = ref('')
const newMember = ref<{ role: string }>({ role: 'member' })
let memberLookupTimer: ReturnType<typeof setTimeout> | null = null

// Debounced exact lookup — one identifier, one answer; never a user listing.
watch(memberIdentifier, (value) => {
  if (memberLookupTimer) clearTimeout(memberLookupTimer)
  memberLookupTimer = setTimeout(
    () => store.lookupMember(props.orgId, value),
    300,
  )
})

onBeforeUnmount(() => {
  if (memberLookupTimer) clearTimeout(memberLookupTimer)
})

const lookupOk = computed(() => store.memberLookup?.status === 'ok')
const lookupDisplayName = computed(() => {
  const found = store.memberLookup
  if (!found?.username) return ''
  return found.fullName
    ? `${found.fullName} (@${found.username})`
    : `@${found.username}`
})

function resetMemberForm(): void {
  if (memberLookupTimer) {
    clearTimeout(memberLookupTimer)
    memberLookupTimer = null
  }
  memberIdentifier.value = ''
  newMember.value = { role: 'member' }
  store.memberError = ''
  store.resetMemberLookup()
}

function openMemberDialog(): void {
  resetMemberForm()
  memberDialogOpen.value = true
}

async function submitAddMember(close: () => void): Promise<void> {
  const found = store.memberLookup
  if (!found || found.status !== 'ok' || !found.userId || store.savingMember) return
  const member = await store.addMember(props.orgId, {
    userId: found.userId,
    role: newMember.value.role,
  })
  if (!member) return
  toast.success(t('tenancy.members.added'))
  close()
}

function confirmRemoveMember(userId: string, name: string): void {
  dialog.danger({
    title: t('tenancy.members.removeTitle'),
    message: t('tenancy.members.removeQuestion', { name }),
    confirmLabel: t('tenancy.members.removeConfirm'),
    onConfirm: async () => {
      const removed = await store.removeMember(props.orgId, userId)
      if (!removed) {
        throw new Error(store.memberError || t('tenancy.errors.removeMember'))
      }
      toast.success(t('tenancy.members.removed'))
    },
  })
}

function load(): void {
  if (!props.orgId) return
  store.memberError = ''
  store.fetchMembers(props.orgId)
}

onMounted(load)
watch(
  () => props.orgId,
  (next, previous) => {
    if (next && next !== previous) load()
  },
)
</script>

<template>
  <div class="flex items-start justify-between gap-3">
    <div class="space-y-1">
      <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.members.title') }}</h2>
      <p class="text-p-sm text-ink-gray-5">{{ t('tenancy.members.description') }}</p>
    </div>
    <Button
      v-if="canManage"
      :label="t('tenancy.members.add')"
      icon-left="lucide-user-plus"
      variant="outline"
      @click="openMemberDialog"
    />
  </div>

  <div>
    <div v-if="store.membersLoading" class="flex justify-center py-10">
      <Spinner />
    </div>
    <ErrorMessage v-else-if="store.membersError" :message="store.membersError" />

    <div
      v-else-if="!store.members.length"
      class="flex flex-col items-center gap-2 py-10 text-center"
    >
      <span class="lucide-users size-8 text-ink-gray-4" aria-hidden="true" />
      <p class="text-p-sm text-ink-gray-5">{{ t('tenancy.members.empty') }}</p>
    </div>

    <List v-else class="list-row-px-3" :columns="memberColumns">
      <ListHead>
        <ListHeaderCell>{{ t('tenancy.members.columnMember') }}</ListHeaderCell>
          <ListHeaderCell>{{ t('tenancy.fields.role') }}</ListHeaderCell>
          <ListHeaderCell v-if="canManage" class="justify-end">
            <span class="sr-only">{{ t('tenancy.members.columnActions') }}</span>
          </ListHeaderCell>
      </ListHead>
      <ListRows :items="store.members" row-key="id" v-slot="{ item }">
        <ListRow :class="LIST_ROW_SURFACE_CLASS">
          <ListCell class="min-w-0">
            <div class="min-w-0">
              <div class="truncate text-base-medium text-ink-gray-8">
                {{ item.fullName || item.username }}
              </div>
              <div v-if="item.fullName" class="truncate text-p-xs text-ink-gray-5">
                {{ item.username }}
              </div>
            </div>
          </ListCell>
          <ListCell>
            <Badge
              :label="roleLabel(item.role)"
              :theme="item.role === 'owner' ? 'violet' : 'gray'"
              variant="subtle"
            />
          </ListCell>
          <ListCell v-if="canManage" class="justify-end">
            <Button
              icon="lucide-trash-2"
              :label="t('tenancy.members.remove')"
              variant="ghost"
              theme="red"
              @click="confirmRemoveMember(item.userId, item.fullName || item.username)"
            />
          </ListCell>
        </ListRow>
      </ListRows>
    </List>
  </div>

  <Dialog
    v-model:open="memberDialogOpen"
    :title="t('tenancy.members.add')"
    icon="lucide-user-plus"
    size="md"
  >
    <div class="space-y-4">
      <FormControl
        v-model="memberIdentifier"
        :label="t('tenancy.members.identifier')"
        :placeholder="t('tenancy.members.identifierPlaceholder')"
        autocomplete="off"
        required
      />
      <div class="space-y-1.5">
        <p v-if="store.memberLookupLoading" class="text-p-sm text-ink-gray-4">
          {{ t('tenancy.members.checking') }}
        </p>
        <Badge
          v-else-if="lookupOk"
          :label="t('tenancy.members.valid', { name: lookupDisplayName })"
          theme="green"
          variant="subtle"
        />
        <Badge
          v-else-if="store.memberLookup?.status === 'already_member'"
          :label="t('tenancy.members.alreadyMember')"
          theme="blue"
          variant="subtle"
        />
        <ErrorMessage
          v-else-if="store.memberLookup?.status === 'not_found'"
          :message="t('tenancy.members.notFound')"
        />
        <ErrorMessage
          v-if="store.memberLookupError"
          :message="store.memberLookupError"
        />
      </div>
      <Select
        v-model="newMember.role"
        :label="t('tenancy.fields.role')"
        :options="roleOptions"
      />
      <ErrorMessage v-if="store.memberError" :message="store.memberError" />
    </div>
    <template #actions="{ close }">
      <div class="flex justify-end gap-2">
        <Button
          :label="t('tenancy.fields.cancel')"
          variant="outline"
          @click="close()"
        />
        <Button
          :label="t('tenancy.members.add')"
          variant="solid"
          theme="gray"
          :loading="store.savingMember"
          :disabled="!lookupOk"
          @click="submitAddMember(close)"
        />
      </div>
    </template>
  </Dialog>
</template>
