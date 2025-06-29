<template>
  <div
    class="fixed top-0 right-0 p-6 z-50 space-y-4"
    style="pointer-events: none"
  >
    <transition-group
      name="notification"
      tag="div"
      class="space-y-4"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        class="notification"
        :class="notificationClass(notification.type)"
        style="pointer-events: auto"
      >
        <div class="flex items-start">
          <div class="flex-shrink-0">
            <component
              :is="getIcon(notification.type)"
              class="h-5 w-5"
            />
          </div>
          <div class="ml-3 w-0 flex-1">
            <p class="text-sm font-medium">
              {{ notification.title }}
            </p>
            <p v-if="notification.message" class="mt-1 text-sm opacity-90">
              {{ notification.message }}
            </p>
          </div>
          <div class="ml-4 flex-shrink-0 flex">
            <button
              @click="removeNotification(notification.id)"
              class="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition ease-in-out duration-150"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { XMarkIcon, CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon } from '@heroicons/vue/24/outline'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

const notifications = ref<Notification[]>([])

const notificationClass = (type: string) => {
  const baseClass = 'max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden p-4'
  
  switch (type) {
    case 'success':
      return `${baseClass} border-l-4 border-green-400 text-green-800`
    case 'error':
      return `${baseClass} border-l-4 border-red-400 text-red-800`
    case 'warning':
      return `${baseClass} border-l-4 border-yellow-400 text-yellow-800`
    case 'info':
    default:
      return `${baseClass} border-l-4 border-blue-400 text-blue-800`
  }
}

const getIcon = (type: string) => {
  switch (type) {
    case 'success':
      return CheckCircleIcon
    case 'error':
      return XCircleIcon
    case 'warning':
      return ExclamationTriangleIcon
    case 'info':
    default:
      return InformationCircleIcon
  }
}

const addNotification = (notification: Omit<Notification, 'id'>) => {
  const id = Math.random().toString(36).substr(2, 9)
  const newNotification = { ...notification, id }
  
  notifications.value.push(newNotification)
  
  // Auto remove after duration (default 5 seconds)
  const duration = notification.duration || 5000
  setTimeout(() => {
    removeNotification(id)
  }, duration)
}

const removeNotification = (id: string) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

// Export functions for use in other components
defineExpose({
  addNotification
})
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style> 