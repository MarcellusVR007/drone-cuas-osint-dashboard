import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue')
    },
    {
      path: '/incidents-map',
      name: 'incidents-map',
      component: () => import('../views/IncidentsMapView.vue')
    },
    {
      path: '/patterns',
      name: 'patterns',
      component: () => import('../views/PatternsView.vue')
    },
    {
      path: '/intel-hub',
      name: 'intel-hub',
      component: () => import('../views/IntelHubView.vue')
    },
    {
      path: '/telegram',
      name: 'telegram',
      component: () => import('../views/TelegramView.vue')
    },
    {
      path: '/forums',
      name: 'forums',
      component: () => import('../views/ForumsView.vue')
    },
    {
      path: '/phone-intel',
      name: 'phone-intel',
      component: () => import('../views/PhoneIntelView.vue')
    },
    {
      path: '/incident/:id',
      name: 'incident-detail',
      component: () => import('../views/IncidentDetailViewNative.vue')
    }
  ]
})

export default router
