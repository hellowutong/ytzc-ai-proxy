import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout/Layout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/',
      component: Layout,
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '仪表盘', icon: 'Odometer' }
        },
        {
          path: 'config',
          name: 'Config',
          component: () => import('@/views/Config.vue'),
          meta: { title: '系统配置', icon: 'Setting' }
        },
        {
          path: 'logs',
          name: 'Logs',
          component: () => import('@/views/Logs.vue'),
          meta: { title: '系统日志', icon: 'Document' }
        },
        {
          path: 'models',
          name: 'Models',
          component: () => import('@/views/VirtualModels.vue'),
          meta: { title: '虚拟模型', icon: 'Cpu' }
        },
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/Chat.vue'),
          meta: { title: '对话管理', icon: 'ChatDotRound' }
        },
        {
          path: 'raw-data',
          name: 'RawData',
          component: () => import('@/views/RawData.vue'),
          meta: { title: '原始数据', icon: 'Files' }
        },
        {
          path: 'knowledge',
          name: 'Knowledge',
          component: () => import('@/views/Knowledge.vue'),
          meta: { title: '知识库', icon: 'Collection' }
        },
        {
          path: 'skill',
          name: 'Skill',
          component: () => import('@/views/Skill.vue'),
          meta: { title: 'Skill', icon: 'Grid' }
        },
        {
          path: 'media',
          name: 'Media',
          component: () => import('@/views/Media.vue'),
          meta: { title: '媒体管理', icon: 'VideoCamera' },
          redirect: '/media/video',
          children: [
            {
              path: 'video',
              name: 'MediaVideo',
              component: () => import('@/views/media/MediaVideo.vue'),
              meta: { title: '视频' }
            },
            {
              path: 'audio',
              name: 'MediaAudio',
              component: () => import('@/views/media/MediaAudio.vue'),
              meta: { title: '音频' }
            },
            {
              path: 'text',
              name: 'MediaText',
              component: () => import('@/views/media/MediaText.vue'),
              meta: { title: '文本&图片' }
            }
          ]
        },
        {
          path: 'rss',
          name: 'RSS',
          component: () => import('@/views/RSS.vue'),
          meta: { title: 'RSS订阅', icon: 'Connection' }
        }
      ]
    }
  ]
})

export default router
