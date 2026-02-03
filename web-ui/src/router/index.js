import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' }
      },
      {
        path: 'connections',
        name: 'Connections',
        component: () => import('@/views/Connections.vue'),
        meta: { title: '连接管理', icon: 'Connection' }
      },
      {
        path: 'sessions',
        name: 'Sessions',
        component: () => import('@/views/Sessions.vue'),
        meta: { title: '会话管理', icon: 'ChatLineRound' }
      },
      {
        path: 'skills',
        name: 'Skills',
        component: () => import('@/views/Skills.vue'),
        meta: { title: '技能管理', icon: 'Star' }
      },
      {
        path: 'vectors',
        name: 'Vectors',
        component: () => import('@/views/Vectors.vue'),
        meta: { title: '向量管理', icon: 'DataLine' }
      },
      {
        path: 'backups',
        name: 'Backups',
        component: () => import('@/views/Backups.vue'),
        meta: { title: '备份管理', icon: 'Folder' }
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('@/views/Config.vue'),
        meta: { title: '系统配置', icon: 'Setting' }
      },
      {
        path: 'baseskills',
        name: 'BaseSkills',
        component: () => import('@/views/BaseSkills.vue'),
        meta: { title: '基础技能', icon: 'Grid' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'TW AI Saver'} - AI 代理中枢`
  next()
})

export default router
