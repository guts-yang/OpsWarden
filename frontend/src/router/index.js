import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { initClient } from '@/api/client'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/AccountsView.vue'),
        meta: { roles: ['admin'] },
      },
      {
        path: 'tickets',
        name: 'Tickets',
        component: () => import('@/views/TicketsView.vue'),
      },
      {
        path: 'chat',
        name: 'AiChat',
        component: () => import('@/views/AiChatView.vue'),
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/KnowledgeBaseView.vue'),
        meta: { roles: ['admin', 'operator'] },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  // Wire up axios client with store + router (idempotent)
  initClient(auth, router)

  if (to.meta.requiresAuth === false) {
    // Public route: redirect to home if already logged in
    if (auth.isLoggedIn && to.name === 'Login') return '/'
    return true
  }
  // Protected route
  if (!auth.isLoggedIn) return '/login'

  const allowedRoles = to.meta.roles
  if (allowedRoles?.length && !allowedRoles.includes(auth.user?.role)) {
    return '/'
  }
  return true
})

export default router
