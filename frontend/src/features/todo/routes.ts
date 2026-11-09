import type { RouteRecordRaw } from 'vue-router'

export const todoRoutes: RouteRecordRaw[] = [
  {
    path: 'todo',
    name: 'ToDo',
    component: () => import('./views/ToDoView.vue'),
    meta: {
      requiresAuth: true,
      title: 'To-dos',
      description: 'Shared task list for the organization.',
    },
  },
]
