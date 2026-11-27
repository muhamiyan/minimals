<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Badge, Button, Spinner } from 'frappe-ui'
import { List, ListCell, ListHeaderCell, ListRow, ListRows } from 'frappe-ui/list'

import AppPageHeader from '@/shared/shell/AppPageHeader.vue'
import ListFoot from '@/shared/components/ListFoot.vue'
import ListHead from '@/shared/components/ListHead.vue'
import ListState from '@/shared/components/ListState.vue'
import ListToolbar from '@/shared/components/ListToolbar.vue'
import { useListControls } from '@/shared/composables/useListControls'
import { formatDate } from '@/shared/format'

import { useBlogStore, type BlogSummary } from '../store'

const { t } = useI18n()
const router = useRouter()
const blog = useBlogStore()

const gateReady = computed(() => blog.checked)
const empty = computed(() => !blog.loading && blog.posts.length === 0)

const columns = {
  base: ['minmax(0,1fr)', '6rem', '3rem'],
  md: ['minmax(0,2fr)', '6rem', '6.5rem', '3rem'],
}

const { search, perPage, reload: refresh, goToPage } = useListControls({
  initialPerPage: blog.perPage,
  setPage: (page) => {
    blog.page = page
  },
  fetch: (query) =>
    blog.fetchAdminList({
      search: query.search,
      page: blog.page,
      perPage: query.perPage,
    }),
})

function openPost(post: BlogSummary) {
  void router.push({ name: 'BlogAdminEdit', params: { slug: post.slug } })
}

onMounted(async () => {
  await refresh()
})
</script>

<template>
  <AppPageHeader>
    <template #default>
      <Button
        variant="solid"
        theme="gray"
        icon-left="lucide-plus"
        :label="t('blog.admin.newPost')"
        :route="{ name: 'BlogAdminCreate' }"
      />
    </template>
    <template #suffix>
      <Button
        variant="ghost"
        theme="gray"
        icon="lucide-plus"
        :label="t('blog.admin.newPost')"
        :route="{ name: 'BlogAdminCreate' }"
      />
    </template>
  </AppPageHeader>

  <div v-if="!gateReady" class="flex justify-center py-10">
    <Spinner />
  </div>

  <div v-else class="mx-auto w-full max-w-6xl space-y-4 px-5 py-6">
    <ListToolbar
      v-model:search="search"
      v-model:per-page="perPage"
      :show-per-page="!empty"
      :placeholder="t('blog.admin.searchPosts')"
    />

    <div>
      <ListState
        :loading="blog.loading"
        :error="blog.error"
        :empty="empty"
        icon="lucide-newspaper"
        :empty-message="search ? t('blog.admin.noPostsFound') : t('blog.empty')"
      >
        <template #action>
          <Button
            variant="outline"
            theme="gray"
            icon-left="lucide-plus"
            :label="t('blog.admin.createFirst')"
            :route="{ name: 'BlogAdminCreate' }"
          />
        </template>

        <List :row-height="32" :columns="columns" class="list-row-px-3">
          <ListHead>
            <ListHeaderCell>{{ t('blog.admin.columns.title') }}</ListHeaderCell>
            <ListHeaderCell>{{ t('blog.admin.columns.status') }}</ListHeaderCell>
            <ListHeaderCell class="max-md:hidden">
              {{ t('blog.admin.columns.created') }}
            </ListHeaderCell>
            <ListHeaderCell class="sr-only">
              {{ t('blog.admin.columns.actions') }}
            </ListHeaderCell>
          </ListHead>

          <ListRows :items="blog.posts" v-slot="{ item }">
            <ListRow :value="item.id" @click="openPost(item)">
              <ListCell>
                <span class="block truncate text-base-medium text-ink-gray-8">
                  {{ item.title }}
                </span>
              </ListCell>
              <ListCell>
                <Badge
                  :label="
                    item.status === 'published'
                      ? t('blog.admin.form.published')
                      : t('blog.admin.form.draft')
                  "
                  :theme="item.status === 'published' ? 'green' : 'gray'"
                  variant="subtle"
                />
              </ListCell>
              <ListCell class="max-md:hidden">
                <span class="truncate text-p-sm text-ink-gray-5">
                  {{ formatDate(item.createdOn) }}
                </span>
              </ListCell>
              <ListCell>
                <Button
                  variant="ghost"
                  theme="gray"
                  icon="lucide-pencil"
                  :label="t('blog.admin.editPost')"
                  @click.stop="openPost(item)"
                />
              </ListCell>
            </ListRow>
          </ListRows>
        </List>
      </ListState>

      <ListFoot
        v-if="!blog.loading && !blog.error && !empty"
        :total="blog.total"
        :page="blog.page"
        :per-page="blog.perPage"
        @update:page="goToPage"
      />
    </div>
  </div>
</template>
