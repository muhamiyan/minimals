<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Badge, Button, ErrorMessage, Select, Spinner, dialog, toast } from 'frappe-ui'
import {
  List,
  ListCell,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'

import ListHead from '@/shared/components/ListHead.vue'
import { formatDate } from '@/shared/format'

import { MEMBER_ROLES, roleLabel, useTenancyStore } from '../store'

const props = defineProps<{ orgId: string }>()

const { t } = useI18n()
const codeColumns = ['minmax(0,1fr)', '90px', '120px', '36px']
const roleOptions = computed(() =>
  MEMBER_ROLES.map((role) => ({ label: roleLabel(role), value: role })),
)

const store = useTenancyStore()

const role = ref('member')
// The most recently generated code — shown once, front and centre, so the
// owner can copy it before it scrolls away into the list.
const freshCode = ref<string | null>(null)

async function generate(): Promise<void> {
  if (store.generatingInvite) return
  const created = await store.generateInviteCode(props.orgId, { role: role.value })
  if (!created) return
  freshCode.value = created.code
  toast.success(t('tenancy.invites.generated'))
}

async function copyCode(code: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(code)
    toast.success(t('tenancy.invites.copied'))
  } catch {
    toast.error(t('tenancy.invites.copyFailed'))
  }
}

function confirmRevoke(id: string, code: string): void {
  dialog.danger({
    title: t('tenancy.invites.revokeTitle'),
    message: t('tenancy.invites.revokeQuestion', { code }),
    confirmLabel: t('tenancy.invites.revokeConfirm'),
    onConfirm: async () => {
      const revoked = await store.revokeInviteCode(props.orgId, id)
      if (!revoked) {
        throw new Error(store.inviteError || t('tenancy.errors.revokeInvite'))
      }
      if (freshCode.value === code) freshCode.value = null
      toast.success(t('tenancy.invites.revoked'))
    },
  })
}

const hasCodes = computed(() => store.inviteCodes.length > 0)

function load(): void {
  if (!props.orgId) return
  store.inviteError = ''
  store.fetchInviteCodes(props.orgId)
}

onMounted(load)
watch(
  () => props.orgId,
  (next, previous) => {
    if (next && next !== previous) {
      freshCode.value = null
      load()
    }
  },
)
onBeforeUnmount(() => {
  freshCode.value = null
})
</script>

<template>
  <div class="flex items-start justify-between gap-3">
    <div class="space-y-1">
      <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.invites.title') }}</h2>
      <p class="text-p-sm text-ink-gray-5">
        {{ t('tenancy.invites.description') }}
      </p>
    </div>
    <div class="flex items-end gap-2">
      <Select v-model="role" :label="t('tenancy.fields.role')" :options="roleOptions" />
      <Button
        :label="t('tenancy.invites.generate')"
        icon-left="lucide-key-round"
        variant="outline"
        :loading="store.generatingInvite"
        @click="generate"
      />
    </div>
  </div>

  <ErrorMessage v-if="store.inviteError" :message="store.inviteError" />

  <div
    v-if="freshCode"
    class="flex items-center justify-between gap-3 rounded-6 border border-outline-gray-1 bg-surface-gray-1 p-3"
  >
    <code class="text-base-semibold tracking-wide text-ink-gray-8">{{ freshCode }}</code>
    <Button
      icon="lucide-copy"
      :label="t('tenancy.invites.copy')"
      variant="ghost"
      @click="copyCode(freshCode)"
    />
  </div>

  <div v-if="store.inviteCodesLoading" class="flex justify-center py-6">
    <Spinner />
  </div>
  <ErrorMessage v-else-if="store.inviteCodesError" :message="store.inviteCodesError" />

  <div
    v-else-if="hasCodes"
    class="overflow-hidden rounded-6 border border-outline-gray-1"
  >
    <List class="list-row-px-3" :columns="codeColumns">
      <ListHead>
        <ListHeaderCell>{{ t('tenancy.invites.columnCode') }}</ListHeaderCell>
        <ListHeaderCell>{{ t('tenancy.fields.role') }}</ListHeaderCell>
        <ListHeaderCell class="hidden sm:flex">
          {{ t('tenancy.invites.columnCreated') }}
        </ListHeaderCell>
        <ListHeaderCell class="justify-end">
          <span class="sr-only">{{ t('tenancy.invites.columnActions') }}</span>
        </ListHeaderCell>
      </ListHead>
      <ListRows :items="store.inviteCodes" row-key="id" v-slot="{ item }">
        <ListRow>
          <ListCell class="min-w-0">
            <div class="flex min-w-0 items-center gap-2">
              <code class="truncate text-base-medium text-ink-gray-8">{{ item.code }}</code>
              <Button
                icon="lucide-copy"
                :label="t('tenancy.invites.copyCode')"
                variant="ghost"
                @click="copyCode(item.code)"
              />
            </div>
          </ListCell>
          <ListCell>
            <Badge
              :label="roleLabel(item.role)"
              :theme="item.role === 'owner' ? 'violet' : 'gray'"
              variant="subtle"
            />
          </ListCell>
          <ListCell class="hidden sm:flex">
            <span class="text-p-sm text-ink-gray-5">{{ formatDate(item.createdOn) }}</span>
          </ListCell>
          <ListCell class="justify-end">
            <Button
              icon="lucide-trash-2"
              :label="t('tenancy.invites.revoke')"
              variant="ghost"
              theme="red"
              @click="confirmRevoke(item.id, item.code)"
            />
          </ListCell>
        </ListRow>
      </ListRows>
    </List>
  </div>

  <p v-else class="text-p-sm text-ink-gray-5">{{ t('tenancy.invites.empty') }}</p>
</template>
