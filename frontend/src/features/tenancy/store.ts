import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { i18n } from '@/app/i18n'
import { useAuthStore } from '@/features/auth/store'
import { api, getErrorMessage } from '@/shared/api'

export const SUB_STATUSES = ['trial', 'active', 'expired', 'cancelled'] as const
export const MEMBER_ROLES = ['owner', 'member'] as const

export type BadgeTheme = 'gray' | 'blue' | 'green' | 'amber' | 'red' | 'violet'

export const TIER_LABELS: Record<string, string> = {
  community: 'Community',
  professional: 'Professional',
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  trial: 'tenancy.status.trial',
  active: 'tenancy.status.active',
  expired: 'tenancy.status.expired',
  cancelled: 'tenancy.status.cancelled',
}

const STATUS_THEMES: Record<string, BadgeTheme> = {
  trial: 'blue',
  active: 'green',
  expired: 'amber',
  cancelled: 'gray',
}

/** Label for a subscription tier; `No subscription` when there is none. */
export function tierLabel(sub: Subscription | null | undefined): string {
  return sub
    ? (TIER_LABELS[sub.tier] ?? sub.tier)
    : i18n.global.t('tenancy.subscription.none')
}

export function tierTheme(sub: Subscription | null | undefined): BadgeTheme {
  return sub?.tier === 'professional' ? 'violet' : 'gray'
}

export function statusLabelFor(status: string): string {
  const key = STATUS_LABEL_KEYS[status]
  return key ? i18n.global.t(key) : status
}

export function roleLabel(role: string): string {
  const key = `tenancy.roles.${role}`
  return i18n.global.te(key) ? i18n.global.t(key) : role
}

export function statusLabel(sub: Subscription | null | undefined): string {
  return sub ? statusLabelFor(sub.status) : i18n.global.t('tenancy.subscription.none')
}

export function statusTheme(sub: Subscription | null | undefined): BadgeTheme {
  return sub ? (STATUS_THEMES[sub.status] ?? 'gray') : 'gray'
}

export interface Subscription {
  id: string
  planId: string
  planName: string
  planDurationValue: number
  planDurationUnit: string
  /** Absent when the plan is billed manually. */
  planPrice?: number | null
  tier: string
  status: string
  featureFlags: Record<string, boolean>
  startedOn: string | null
  expiresOn: string | null
}

export interface Organization {
  id: string
  name: string
  slug: string
  isActive: boolean
  createdOn: string | null
  subscription: Subscription | null
  memberCount: number
  /** Only present on `/my-organizations` items; absent on the console list. */
  myRole?: string | null
}

export interface Member {
  id: string
  userId: string
  username: string
  fullName: string
  role: string
  createdOn: string | null
}

/** Result of `/tenancy/organizations/:id/user-lookup` — one exact match, never a list.
 *  Presenters omit null fields: `userId`/`username`/`fullName` are absent on `not_found`. */
export interface MemberLookup {
  status: 'ok' | 'already_member' | 'not_found'
  userId?: string | null
  username?: string | null
  fullName?: string | null
}

/** Owner-generated code; the raw value is shown once and revocable. */
export interface InviteCode {
  id: string
  code: string
  role: string
  createdOn: string | null
}

/** Result of `POST /tenancy/invites/redeem` — which org the caller joined. */
export interface InviteRedeemResult {
  organizationId: string
  name: string
  slug: string
  role: string
  alreadyMember: boolean
}

export interface SubscriptionInput {
  planId: string
  status: string
  expiresOn?: string
}

interface Paged<T> {
  items: T[]
  total: number
  page: number
  perPage: number
}

const ACTIVE_ORG_STORAGE_PREFIX = 'minimals-active-org:'

function activeOrgStorageKey(userId: string | null | undefined): string | null {
  return userId ? `${ACTIVE_ORG_STORAGE_PREFIX}${userId}` : null
}

function readStoredActiveOrg(userId: string | null | undefined): string | null {
  const key = activeOrgStorageKey(userId)
  if (!key) return null
  try {
    return sessionStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStoredActiveOrg(
  userId: string | null | undefined,
  orgId: string | null,
): void {
  const key = activeOrgStorageKey(userId)
  if (!key) return
  try {
    if (orgId) sessionStorage.setItem(key, orgId)
    else sessionStorage.removeItem(key)
  } catch {
    return
  }
}

/**
 * Drop every organization choice held by this tab. Signing out must not
 * leave a selection behind: the next sign-in starts from `default_org_id`.
 */
function clearStoredActiveOrg(): void {
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i -= 1) {
      const key = sessionStorage.key(i)
      if (key?.startsWith(ACTIVE_ORG_STORAGE_PREFIX)) sessionStorage.removeItem(key)
    }
  } catch {
    return
  }
}

export const useTenancyStore = defineStore('tenancy', () => {
  const auth = useAuthStore()

  // organizations list
  const items = ref<Organization[]>([])
  const total = ref(0)
  const page = ref(1)
  const listLoading = ref(false)
  const listError = ref('')
  const createError = ref('')

  // organization detail
  const current = ref<Organization | null>(null)
  const orgLoading = ref(false)
  const orgError = ref('')
  const orgSaveError = ref('')

  // subscription
  const subSaveError = ref('')

  // features
  const features = ref<Record<string, boolean>>({})
  const featuresLoading = ref(false)
  const featuresError = ref('')

  // members
  const members = ref<Member[]>([])
  const membersLoading = ref(false)
  const membersError = ref('')
  const memberError = ref('')
  const savingMember = ref(false)

  // member lookup (add-member form: one identifier, one answer)
  const memberLookup = ref<MemberLookup | null>(null)
  const memberLookupLoading = ref(false)
  const memberLookupError = ref('')
  let memberLookupSeq = 0

  // the signed-in user's own organizations (tenant-facing)
  const myOrgs = ref<Organization[]>([])
  const defaultOrgId = ref<string | null>(null)
  const activeOrgId = ref<string | null>(null)
  const myOrgsLoading = ref(false)
  const myOrgsError = ref('')
  // True once a fetch has succeeded — the router guard uses it so the
  // onboarding gate doesn't re-request on every navigation.
  const myOrgsLoaded = ref(false)
  const switchingOrg = ref(false)

  // self-service onboarding: create own organization / redeem an invite code
  const creatingOwnOrg = ref(false)
  const createOwnError = ref('')
  const redeemingInvite = ref(false)
  const redeemError = ref('')

  // invite codes (owner panel)
  const inviteCodes = ref<InviteCode[]>([])
  const inviteCodesLoading = ref(false)
  const inviteCodesError = ref('')
  const inviteError = ref('')
  const generatingInvite = ref(false)

  // platform settings (superadmin console — global member quota)
  const settingsMembersLimit = ref<number | null>(null)
  const settingsLoading = ref(false)
  const settingsError = ref('')
  const settingsSaving = ref(false)
  const settingsSaveError = ref('')
  // In-flight promises so AppShell + Dashboard + views can all ask for the
  // same data on first load without firing duplicate requests.
  let myOrgsInFlight: Promise<void> | null = null
  let activeFeaturesInFlight: Promise<void> | null = null
  let activeFeaturesOrgId: string | null = null

  // Stale-response guards: org switches (or logout) must not let a late
  // response overwrite the state of the org the user moved on to.
  let myOrgsSeq = 0
  let orgSeq = 0
  let membersSeq = 0
  let activeFeaturesSeq = 0
  let inviteCodesSeq = 0

  // features of `currentOrg`, gated for the tenant-facing UI
  const activeFeatures = ref<Record<string, boolean>>({})
  const activeFeaturesLoading = ref(false)
  const activeFeaturesError = ref('')

  function invalidateActiveFeatures(): void {
    activeFeaturesSeq += 1
    activeFeaturesOrgId = null
    activeFeaturesInFlight = null
    activeFeatures.value = {}
    activeFeaturesError.value = ''
    activeFeaturesLoading.value = false
  }

  function resolveActiveOrgId(): string | null {
    if (!myOrgs.value.length) return null
    const ids = new Set(myOrgs.value.map((org) => org.id))
    if (activeOrgId.value && ids.has(activeOrgId.value)) return activeOrgId.value
    if (defaultOrgId.value && ids.has(defaultOrgId.value)) return defaultOrgId.value
    return myOrgs.value[0].id
  }

  /** The organization the tenant-facing UI acts on. */
  const currentOrg = computed<Organization | null>(() => {
    const orgId = resolveActiveOrgId()
    return orgId ? (myOrgs.value.find((org) => org.id === orgId) ?? null) : null
  })

  function setActiveOrg(orgId: string): boolean {
    if (!myOrgs.value.some((org) => org.id === orgId)) return false
    if (activeOrgId.value === orgId) return true
    activeOrgId.value = orgId
    writeStoredActiveOrg(auth.user?.id, orgId)
    invalidateActiveFeatures()
    return true
  }

  async function fetchList(query: { search: string; perPage: number }): Promise<void> {
    listLoading.value = true
    listError.value = ''
    try {
      const { data } = await api.get<Paged<Organization>>('/tenancy/organizations', {
        params: {
          search: query.search.trim() || undefined,
          page: page.value,
          per_page: query.perPage,
        },
      })
      items.value = data.items ?? []
      total.value = data.total ?? 0
      page.value = data.page ?? page.value
    } catch (e: any) {
      listError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.list'))
    } finally {
      listLoading.value = false
    }
  }

  function setPage(next: number): void {
    page.value = next
  }

  async function createOrganization(
    payload: { name: string; slug: string },
  ): Promise<Organization | null> {
    createError.value = ''
    try {
      const { data } = await api.post<Organization>('/tenancy/organizations', payload)
      return data
    } catch (e: any) {
      createError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.create'))
      return null
    }
  }

  async function fetchOrg(id: string): Promise<Organization | null> {
    const seq = ++orgSeq
    orgLoading.value = true
    orgError.value = ''
    if (current.value?.id !== id) current.value = null
    try {
      const { data } = await api.get<Organization>(`/tenancy/organizations/${id}`)
      if (seq !== orgSeq) return null
      current.value = data
      return data
    } catch (e: any) {
      if (seq !== orgSeq) return null
      orgError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.org'))
      return null
    } finally {
      if (seq === orgSeq) orgLoading.value = false
    }
  }

  async function updateOrg(
    id: string,
    payload: { name: string; slug: string; isActive: boolean },
  ): Promise<Organization | null> {
    orgSeq++ // a fresh save outranks any in-flight fetchOrg
    orgSaveError.value = ''
    try {
      const { data } = await api.patch<Organization>(
        `/tenancy/organizations/${id}`,
        payload,
      )
      current.value = data
      return data
    } catch (e: any) {
      orgSaveError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.saveOrg'))
      return null
    }
  }

  async function saveSubscription(
    id: string,
    payload: SubscriptionInput,
  ): Promise<Subscription | null> {
    orgSeq++ // a fresh save outranks any in-flight fetchOrg
    subSaveError.value = ''
    try {
      const { data } = await api.put<Subscription>(
        `/tenancy/organizations/${id}/subscription`,
        payload,
      )
      if (current.value && current.value.id === id) {
        current.value.subscription = data
      }
      return data
    } catch (e: any) {
      subSaveError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.saveSubscription'))
      return null
    }
  }

  async function fetchFeatures(id: string): Promise<void> {
    featuresLoading.value = true
    featuresError.value = ''
    features.value = {}
    try {
      const { data } = await api.get<{ features: Record<string, boolean> }>(
        `/tenancy/organizations/${id}/features`,
      )
      features.value = data.features ?? {}
    } catch (e: any) {
      featuresError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.features'))
    } finally {
      featuresLoading.value = false
    }
  }

  async function fetchMembers(id: string): Promise<void> {
    const seq = ++membersSeq
    membersLoading.value = true
    membersError.value = ''
    members.value = []
    try {
      const { data } = await api.get<{ items: Member[] }>(
        `/tenancy/organizations/${id}/members`,
      )
      if (seq !== membersSeq) return
      members.value = data.items ?? []
    } catch (e: any) {
      if (seq !== membersSeq) return
      membersError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.members'))
    } finally {
      if (seq === membersSeq) membersLoading.value = false
    }
  }

  async function addMember(
    id: string,
    payload: { userId: string; role: string },
  ): Promise<Member | null> {
    memberError.value = ''
    savingMember.value = true
    try {
      const { data } = await api.post<Member>(
        `/tenancy/organizations/${id}/members`,
        payload,
      )
      members.value = [...members.value, data]
      bumpMemberCount(id, 1)
      return data
    } catch (e: any) {
      memberError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.addMember'))
      return null
    } finally {
      savingMember.value = false
    }
  }

  async function removeMember(id: string, userId: string): Promise<boolean> {
    memberError.value = ''
    try {
      await api.delete(`/tenancy/organizations/${id}/members/${userId}`)
      members.value = members.value.filter((m) => m.userId !== userId)
      bumpMemberCount(id, -1)
      return true
    } catch (e: any) {
      memberError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.removeMember'))
      return false
    }
  }

  // Adjusted in place so an untouched edit form on the detail view is not
  // clobbered by refetching the whole organization.
  function bumpMemberCount(id: string, delta: number): void {
    if (current.value && current.value.id === id) {
      current.value.memberCount = Math.max(0, current.value.memberCount + delta)
    }
  }

  async function lookupMember(orgId: string, identifier: string): Promise<void> {
    const seq = ++memberLookupSeq
    const trimmed = identifier.trim()
    if (!orgId || !trimmed) {
      memberLookup.value = null
      memberLookupLoading.value = false
      memberLookupError.value = ''
      return
    }
    memberLookup.value = null // a stale answer must never enable Add
    memberLookupLoading.value = true
    memberLookupError.value = ''
    try {
      const { data } = await api.get<MemberLookup>(
        `/tenancy/organizations/${orgId}/user-lookup`,
        { params: { identifier: trimmed } },
      )
      if (seq !== memberLookupSeq) return
      memberLookup.value = data
    } catch (e: any) {
      if (seq !== memberLookupSeq) return
      memberLookupError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.lookup'))
    } finally {
      if (seq === memberLookupSeq) memberLookupLoading.value = false
    }
  }

  function resetMemberLookup(): void {
    memberLookupSeq++
    memberLookup.value = null
    memberLookupLoading.value = false
    memberLookupError.value = ''
  }

  // --- tenant-facing: my organizations --------------------------------
  function fetchMyOrgs(): Promise<void> {
    if (myOrgsInFlight) return myOrgsInFlight
    const seq = ++myOrgsSeq
    myOrgsInFlight = (async () => {
      myOrgsLoading.value = true
      myOrgsError.value = ''
      try {
        const { data } = await api.get<{
          items: Organization[]
          defaultId: string | null
        }>('/tenancy/my-organizations')
        if (seq !== myOrgsSeq) return
        const previousOrgId = currentOrg.value?.id ?? null
        myOrgs.value = data.items ?? []
        defaultOrgId.value = data.defaultId ?? null
        const stored = readStoredActiveOrg(auth.user?.id)
        const ids = new Set(myOrgs.value.map((org) => org.id))
        activeOrgId.value =
          (stored && ids.has(stored) ? stored : null) ??
          (activeOrgId.value && ids.has(activeOrgId.value) ? activeOrgId.value : null) ??
          (defaultOrgId.value && ids.has(defaultOrgId.value) ? defaultOrgId.value : null) ??
          myOrgs.value[0]?.id ??
          null
        if (stored && stored !== activeOrgId.value) {
          writeStoredActiveOrg(auth.user?.id, null)
        }
        if ((currentOrg.value?.id ?? null) !== previousOrgId) {
          invalidateActiveFeatures()
        }
        myOrgsLoaded.value = true
      } catch (e: any) {
        if (seq !== myOrgsSeq) return
        myOrgsError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.myOrgs'))
      } finally {
        if (seq === myOrgsSeq) myOrgsLoading.value = false
      }
    })().finally(() => {
      // Only the newest run may unblock the dedupe slot — an older one
      // settling late must not evict the promise that replaced it.
      if (seq === myOrgsSeq) myOrgsInFlight = null
    })
    return myOrgsInFlight
  }

  /**
   * Force a fresh `/my-organizations`. Used after mutations (create/redeem)
   * and when entering onboarding: the dedupe slot may be held by a request
   * that started *before* the change, which would answer with a stale list.
   */
  function refreshMyOrgs(): Promise<void> {
    myOrgsSeq++ // a stale in-flight response must not satisfy this refresh
    myOrgsInFlight = null
    return fetchMyOrgs()
  }

  async function setDefaultOrg(orgId: string): Promise<boolean> {
    if (switchingOrg.value) return false
    myOrgsError.value = ''
    switchingOrg.value = true
    try {
      const { data } = await api.put<{ defaultId: string }>(
        '/tenancy/my-organizations/default',
        { orgId },
      )
      const previousOrgId = currentOrg.value?.id ?? null
      defaultOrgId.value = data.defaultId ?? orgId
      if ((currentOrg.value?.id ?? null) !== previousOrgId) {
        invalidateActiveFeatures()
      }
      return true
    } catch (e: any) {
      myOrgsError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.switchOrg'))
      return false
    } finally {
      switchingOrg.value = false
    }
  }

  // --- tenant-facing: onboarding (create own org / redeem invite) ------
  async function createOwnOrganization(
    payload: { name: string; slug: string },
  ): Promise<Organization | null> {
    createOwnError.value = ''
    creatingOwnOrg.value = true
    try {
      const { data } = await api.post<Organization>(
        '/tenancy/my-organizations',
        payload,
      )
      await refreshMyOrgs()
      return data
    } catch (e: any) {
      createOwnError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.create'))
      return null
    } finally {
      creatingOwnOrg.value = false
    }
  }

  async function redeemInvite(code: string): Promise<InviteRedeemResult | null> {
    redeemError.value = ''
    redeemingInvite.value = true
    try {
      const { data } = await api.post<InviteRedeemResult>(
        '/tenancy/invites/redeem',
        { code: code.trim().toUpperCase() },
      )
      await refreshMyOrgs()
      return data
    } catch (e: any) {
      redeemError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.redeem'))
      return null
    } finally {
      redeemingInvite.value = false
    }
  }

  // --- tenant-facing: invite codes (owner) ------------------------------
  async function fetchInviteCodes(orgId: string): Promise<void> {
    const seq = ++inviteCodesSeq
    inviteCodesLoading.value = true
    inviteCodesError.value = ''
    inviteCodes.value = []
    try {
      const { data } = await api.get<{ items: InviteCode[] }>(
        `/tenancy/organizations/${orgId}/invite-codes`,
      )
      if (seq !== inviteCodesSeq) return
      inviteCodes.value = data.items ?? []
    } catch (e: any) {
      if (seq !== inviteCodesSeq) return
      inviteCodesError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.inviteCodes'))
    } finally {
      if (seq === inviteCodesSeq) inviteCodesLoading.value = false
    }
  }

  async function generateInviteCode(
    orgId: string,
    payload: { role: string },
  ): Promise<InviteCode | null> {
    inviteError.value = ''
    generatingInvite.value = true
    try {
      const { data } = await api.post<InviteCode>(
        `/tenancy/organizations/${orgId}/invite-codes`,
        payload,
      )
      inviteCodes.value = [data, ...inviteCodes.value]
      return data
    } catch (e: any) {
      inviteError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.generateInvite'))
      return null
    } finally {
      generatingInvite.value = false
    }
  }

  async function revokeInviteCode(orgId: string, codeId: string): Promise<boolean> {
    inviteError.value = ''
    try {
      await api.delete(`/tenancy/organizations/${orgId}/invite-codes/${codeId}`)
      inviteCodes.value = inviteCodes.value.filter((code) => code.id !== codeId)
      return true
    } catch (e: any) {
      inviteError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.revokeInvite'))
      return false
    }
  }

  // --- platform settings (superadmin) ------------------------------------
  /** Always fetches fresh: another admin may have changed the quota. */
  async function fetchSettings(): Promise<number | null> {
    settingsLoading.value = true
    settingsError.value = ''
    settingsSaveError.value = ''
    try {
      const { data } = await api.get<{ membersLimit: number }>('/tenancy/settings')
      settingsMembersLimit.value = data.membersLimit
      return data.membersLimit
    } catch (e: any) {
      settingsError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.loadSettings'))
      return null
    } finally {
      settingsLoading.value = false
    }
  }

  async function updateMembersLimit(membersLimit: number): Promise<boolean> {
    settingsSaveError.value = ''
    settingsSaving.value = true
    try {
      const { data } = await api.put<{ membersLimit: number }>('/tenancy/settings', {
        membersLimit,
      })
      settingsMembersLimit.value = data.membersLimit
      return true
    } catch (e: any) {
      settingsSaveError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.saveSettings'))
      return false
    } finally {
      settingsSaving.value = false
    }
  }

  function fetchActiveFeatures(): Promise<void> {
    const orgId = currentOrg.value?.id ?? null
    if (activeFeaturesInFlight && activeFeaturesOrgId === orgId) {
      return activeFeaturesInFlight
    }
    if (!orgId) {
      invalidateActiveFeatures()
      return Promise.resolve()
    }
    const seq = ++activeFeaturesSeq
    activeFeaturesOrgId = orgId
    activeFeaturesLoading.value = true
    activeFeaturesError.value = ''
    const request = api
      .get<{ features: Record<string, boolean> }>(
        `/tenancy/organizations/${orgId}/features`,
      )
      .then(({ data }) => {
        if (seq !== activeFeaturesSeq) return
        activeFeatures.value = data.features ?? {}
      })
      .catch((e: any) => {
        if (seq !== activeFeaturesSeq) return
        activeFeaturesError.value = getErrorMessage(e, i18n.global.t('tenancy.errors.features'))
      })
      .finally(() => {
        if (seq !== activeFeaturesSeq) return
        activeFeaturesLoading.value = false
        activeFeaturesInFlight = null
        activeFeaturesOrgId = null
      })
    activeFeaturesInFlight = request
    return request
  }

  function hasFeature(flag: string): boolean {
    return activeFeatures.value[flag] === true
  }

  /**
   * Drop tenant-facing state so a re-login never shows the previous user or
   * the organization they last picked — the next sign-in starts from the
   * default again.
   */
  function resetMyOrgs(): void {
    clearStoredActiveOrg()
    myOrgsSeq++
    orgSeq++
    membersSeq++
    activeFeaturesSeq++
    inviteCodesSeq++
    // Unblock fresh fetches; the seq bumps make the old ones no-ops.
    myOrgsInFlight = null
    activeFeaturesInFlight = null
    myOrgs.value = []
    defaultOrgId.value = null
    activeOrgId.value = null
    myOrgsError.value = ''
    myOrgsLoading.value = false
    myOrgsLoaded.value = false
    switchingOrg.value = false
    createOwnError.value = ''
    creatingOwnOrg.value = false
    redeemError.value = ''
    redeemingInvite.value = false
    inviteCodes.value = []
    inviteCodesLoading.value = false
    inviteCodesError.value = ''
    inviteError.value = ''
    generatingInvite.value = false
    settingsMembersLimit.value = null
    settingsLoading.value = false
    settingsError.value = ''
    settingsSaving.value = false
    settingsSaveError.value = ''
    activeFeatures.value = {}
    activeFeaturesLoading.value = false
    activeFeaturesError.value = ''
    activeFeaturesOrgId = null
  }

  return {
    items,
    total,
    page,
    listLoading,
    listError,
    createError,
    current,
    orgLoading,
    orgError,
    orgSaveError,
    subSaveError,
    features,
    featuresLoading,
    featuresError,
    members,
    membersLoading,
    membersError,
    memberError,
    savingMember,
    memberLookup,
    memberLookupLoading,
    memberLookupError,
    myOrgs,
    defaultOrgId,
    activeOrgId,
    myOrgsLoading,
    myOrgsError,
    myOrgsLoaded,
    switchingOrg,
    creatingOwnOrg,
    createOwnError,
    redeemingInvite,
    redeemError,
    inviteCodes,
    inviteCodesLoading,
    inviteCodesError,
    inviteError,
    generatingInvite,
    settingsMembersLimit,
    settingsLoading,
    settingsError,
    settingsSaving,
    settingsSaveError,
    activeFeatures,
    activeFeaturesLoading,
    activeFeaturesError,
    currentOrg,
    fetchList,
    setPage,
    createOrganization,
    fetchOrg,
    updateOrg,
    saveSubscription,
    fetchFeatures,
    fetchMembers,
    addMember,
    removeMember,
    lookupMember,
    resetMemberLookup,
    fetchMyOrgs,
    refreshMyOrgs,
    setActiveOrg,
    setDefaultOrg,
    createOwnOrganization,
    redeemInvite,
    fetchInviteCodes,
    generateInviteCode,
    revokeInviteCode,
    fetchSettings,
    updateMembersLimit,
    fetchActiveFeatures,
    hasFeature,
    resetMyOrgs,
  }
})
