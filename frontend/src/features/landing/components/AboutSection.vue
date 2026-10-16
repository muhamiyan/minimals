<script setup lang="ts">
import { Badge } from 'frappe-ui'

import { principles } from '../content'
</script>

<template>
  <section id="about" class="border-t border-outline-gray-1">
    <div class="mx-auto grid w-full max-w-6xl gap-10 px-5 py-20 lg:grid-cols-5">
      <div class="lg:col-span-3">
        <Badge theme="blue" variant="outline" label="About" />
        <h2 class="mt-4 text-5xl-bold text-ink-gray-9">Minimal, not trivial.</h2>
        <div class="mt-5 max-w-xl space-y-4 text-p-base text-ink-gray-6">
          <p>
            Minimals started from an observation: every production Flask
            service re-implements the same scaffolding — auth, CSRF, roles,
            migrations, health checks, a frontend build. Minimals packages that
            floor, and nothing above it.
          </p>
          <p>
            The architecture is deliberately boring. Services own
            transactions, repositories own queries, and the wire format is a
            tested contract. When something breaks, you fix it at the point of
            failure — there is no history to dig through.
          </p>
        </div>
      </div>

      <div class="lg:col-span-2">
        <div class="rounded-6 border border-outline-gray-1 bg-surface-elevation-2 p-5">
          <div class="flex items-center gap-2 text-base-semibold text-ink-gray-8">
            <span class="lucide-badge-check size-4 text-ink-blue-7" aria-hidden="true" />
            House rules
          </div>
          <ul class="mt-4 space-y-3">
            <li
              v-for="rule in principles"
              :key="rule"
              class="flex gap-2.5 text-p-sm text-ink-gray-6"
            >
              <span
                class="lucide-check mt-0.5 size-4 shrink-0 text-ink-green-6"
                aria-hidden="true"
              />
              <span>{{ rule }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>
