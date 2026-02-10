import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layouts/AdminLayout.vue'
import ProxyLayout from '@/layouts/ProxyLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/admin/dashboard'
    },
    {
      path: '/proxy',
      component: ProxyLayout,
      children: [
        {
          path: 'chat',
          name: 'WebChat',
          component: () => import('@/views/proxy/WebChat.vue')
        }
      ]
    },
    {
      path: '/admin',
      component: AdminLayout,
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/admin/Dashboard.vue')
        },
        {
          path: 'models',
          name: 'VirtualModels',
          component: () => import('@/views/admin/VirtualModels.vue')
        },
        {
          path: 'skills',
          name: 'Skills',
          component: () => import('@/views/admin/Skills.vue')
        },
        {
          path: 'conversations',
          name: 'Conversations',
          component: () => import('@/views/admin/Conversations.vue')
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('@/views/admin/Knowledge.vue')
        },
        {
          path: 'media',
          name: 'Media',
          component: () => import('@/views/admin/Media.vue')
        },
        {
          path: 'rss',
          name: 'RSS',
          component: () => import('@/views/admin/RSS.vue')
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('@/views/admin/Logs.vue')
        },
        {
          path: 'config',
          name: 'Config',
          component: () => import('@/views/admin/Config.vue')
        },
        {
          path: 'raw-data',
          name: 'RawData',
          component: () => import('@/views/admin/RawData.vue')
        }
      ]
    }
  ]
})

export default router
