import type { RouteRecordRaw } from 'vue-router'

export const todosRoutes: RouteRecordRaw[] = [
  {
    path: 'todos',
    name: 'ToDos',
    component: () => import('./views/ToDosView.vue'),
    meta: {
      requiresAuth: true,
      title: 'To-dos',
      description: 'Shared task list for the organization.',
    },
  },
]
