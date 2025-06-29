import { createRouter, createWebHistory } from 'vue-router'

// Lazy load route components for better performance and code splitting
const ChatView = () => import('@/views/ChatView.vue')
const TasksView = () => import('@/views/TasksView.vue')
const AwsView = () => import('@/views/AwsView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'new-chat',
      component: ChatView,
      meta: {
        title: 'New Chat'
      }
    },
    {
      path: '/chat/:id',
      name: 'chat',
      component: ChatView,
      meta: {
        title: 'Chat'
      },
      props: true
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: TasksView,
      meta: {
        title: 'Tasks'
      }
    },
    {
      path: '/aws',
      name: 'aws',
      component: AwsView,
      meta: {
        title: 'AWS'
      }
    }
  ]
})

router.beforeEach((to) => {
  document.title = `${to.meta.title} - AWS Cloud Engineer Agent`
})

export default router 