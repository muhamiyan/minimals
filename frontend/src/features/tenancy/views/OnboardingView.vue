<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'

import { useTenancyStore } from '../store'
import { slugify, validateName, validateSlug } from '../validation'

type Choice = 'create' | 'redeem'

const router = useRouter()
const { t } = useI18n()
const store = useTenancyStore()

// Step 1 picks a card; step 2 shows only that form — never both at once.
const choice = ref<Choice | null>(null)

const name = ref('')
const slug = ref('')
const slugTouched = ref(false)
const nameError = ref('')
const slugError = ref('')

const code = ref('')

watch(
  () => name.value,
  (value) => {
    if (slugTouched.value) return
    slug.value = slugify(value)
  },
  { flush: 'sync' },
)

const busy = computed(() => store.creatingOwnOrg || store.redeemingInvite)

function pick(next: Choice): void {
  choice.value = next
}

function back(): void {
  choice.value = null
  // Field values survive an accidental back; only the errors are cleared.
  nameError.value = ''
  slugError.value = ''
  store.createOwnError = ''
  store.redeemError = ''
}

function onSlugInput(value: unknown): void {
  slug.value = String(value ?? '')
  slugTouched.value = true
}

/**
 * The gate memoizes the empty list, so someone who was just added by an owner
 * (add-member dialog, not a code) needs a way out without a hard reload.
 */
async function checkAgain(): Promise<void> {
  if (busy.value || store.myOrgsLoading) return
  await store.refreshMyOrgs()
  if (store.myOrgsError) return // shown in the ErrorMessage under the button
  if (store.myOrgs.length) {
    toast.success(t('tenancy.onboarding.checkFound'))
    await router.replace({ name: 'Dashboard' })
  } else {
    toast.info(t('tenancy.onboarding.checkNotFound'))
  }
}

onMounted(async () => {
  // Fresh data on entry: the guard's answer may already be stale, and a
  // list that just gained an org must not strand the user here.
  await store.refreshMyOrgs()
  if (store.myOrgs.length) await router.replace({ name: 'Dashboard' })
})

async function submitCreate(): Promise<void> {
  if (busy.value) return
  nameError.value = validateName(name.value)
  slugError.value = validateSlug(slug.value)
  if (nameError.value || slugError.value) return

  const org = await store.createOwnOrganization({
    name: name.value.trim(),
    slug: slug.value.trim().toLowerCase(),
  })
  if (!org) return

  toast.success(t('tenancy.onboarding.created', { name: org.name }))
  await router.replace({ name: 'MyOrganization', params: { orgId: org.id } })
}

async function submitRedeem(): Promise<void> {
  if (busy.value || !code.value.trim()) return
  const result = await store.redeemInvite(code.value)
  if (!result) return

  if (result.alreadyMember) {
    toast.info(t('tenancy.onboarding.alreadyMember', { name: result.name }))
  } else {
    toast.success(t('tenancy.onboarding.joined', { name: result.name }))
  }
  await router.replace({ name: 'Dashboard' })
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-base p-4 text-ink-gray-8">
    <div class="w-full max-w-3xl space-y-6">
      <div class="flex flex-col items-center gap-1.5 text-center">
        <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
          <span class="lucide-building size-6" aria-hidden="true" />
        </div>
        <h1 class="text-2xl-semibold text-ink-gray-8">{{ t('tenancy.onboarding.welcome') }}</h1>
        <p class="text-p-sm text-ink-gray-5">
          {{ t('tenancy.onboarding.intro') }}
        </p>
      </div>

      <!-- Step 1: choose how to continue. Native <button> cards — there is no
           frappe-ui Card component; the global :focus-visible outline still
           applies, and all colors come from theme tokens. -->
      <div v-if="!choice" class="grid gap-4 sm:grid-cols-2">
        <button
          type="button"
          class="space-y-2 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 text-left transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
          @click="pick('create')"
        >
          <span class="lucide-building-2 size-6 text-ink-gray-6" aria-hidden="true" />
          <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.onboarding.newOrg') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('tenancy.onboarding.newOrgDescription') }}
          </p>
        </button>

        <button
          type="button"
          class="space-y-2 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5 text-left transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-1"
          @click="pick('redeem')"
        >
          <span class="lucide-key-round size-6 text-ink-gray-6" aria-hidden="true" />
          <h2 class="text-base-medium text-ink-gray-8">{{ t('tenancy.onboarding.invite') }}</h2>
          <p class="text-p-sm text-ink-gray-5">
            {{ t('tenancy.onboarding.inviteDescription') }}
          </p>
        </button>
      </div>

      <!-- Step 2: only the chosen form -->
      <section
        v-else
        class="mx-auto w-full max-w-md space-y-4 rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5"
      >
        <div class="flex items-center gap-2">
          <Button
            icon="lucide-arrow-left"
            :label="t('tenancy.onboarding.back')"
            variant="ghost"
            :disabled="busy"
            @click="back"
          />
          <h2 class="text-base-medium text-ink-gray-8">
            {{
              choice === 'create'
                ? t('tenancy.onboarding.newOrg')
                : t('tenancy.onboarding.invite')
            }}
          </h2>
        </div>

        <form v-if="choice === 'create'" class="space-y-4" @submit.prevent="submitCreate">
          <ErrorMessage v-if="store.createOwnError" :message="store.createOwnError" />
          <FormControl
            v-model="name"
            :label="t('tenancy.fields.name')"
            :placeholder="t('tenancy.fields.namePlaceholder')"
            required
            :error="nameError"
          />
          <FormControl
            :model-value="slug"
            :label="t('tenancy.fields.slug')"
            :description="t('tenancy.fields.slugDescription')"
            :placeholder="t('tenancy.fields.slugPlaceholder')"
            required
            :error="slugError"
            @update:model-value="onSlugInput"
          />
          <Button
            type="submit"
            :label="t('tenancy.onboarding.createSubmit')"
            icon-left="lucide-building"
            variant="solid"
            theme="gray"
            :loading="store.creatingOwnOrg"
          />
        </form>

        <form v-else class="space-y-4" @submit.prevent="submitRedeem">
          <ErrorMessage v-if="store.redeemError" :message="store.redeemError" />
          <FormControl
            v-model="code"
            :label="t('tenancy.onboarding.code')"
            :placeholder="t('tenancy.onboarding.codePlaceholder')"
            autocomplete="off"
            required
          />
          <Button
            type="submit"
            :label="t('tenancy.onboarding.joinSubmit')"
            icon-left="lucide-key-round"
            variant="solid"
            theme="gray"
            :loading="store.redeemingInvite"
            :disabled="!code.trim()"
          />
        </form>
      </section>

      <div v-if="!choice" class="space-y-3">
        <p class="text-center text-p-sm text-ink-gray-5">
          {{ t('tenancy.onboarding.checkQuestion') }}
          <Button
            class="-ml-2"
            :label="t('tenancy.onboarding.checkAgain')"
            variant="ghost"
            :loading="store.myOrgsLoading"
            :disabled="busy"
            @click="checkAgain"
          />
        </p>
        <!-- Refresh failures (mount or Check again) surface here — nothing
             else on this page reports them. -->
        <ErrorMessage v-if="store.myOrgsError" :message="store.myOrgsError" />
      </div>
    </div>
  </div>
</template>
