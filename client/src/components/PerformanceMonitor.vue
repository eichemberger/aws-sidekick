<template>
  <div v-if="isDev" class="fixed bottom-4 right-4 bg-gray-800 border border-gray-600 rounded-lg p-3 text-xs text-gray-300 font-mono z-50">
    <div class="space-y-1">
      <div>FPS: {{ fps }}</div>
      <div>Memory: {{ memoryUsage }}MB</div>
      <div>Components: {{ componentCount }}</div>
      <div>Bundle: {{ bundleSize }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isDev = import.meta.env.DEV
const fps = ref(0)
const memoryUsage = ref(0)
const componentCount = ref(0)
const bundleSize = ref('~500KB')

let animationId: number | null = null
let lastTime = performance.now()
let frameCount = 0

const updateFPS = () => {
  const currentTime = performance.now()
  frameCount++
  
  if (currentTime - lastTime >= 1000) {
    fps.value = Math.round((frameCount * 1000) / (currentTime - lastTime))
    frameCount = 0
    lastTime = currentTime
  }
  
  animationId = requestAnimationFrame(updateFPS)
}

const updateMemoryUsage = () => {
  if ('memory' in performance) {
    const memory = (performance as any).memory
    memoryUsage.value = Math.round(memory.usedJSHeapSize / 1024 / 1024)
  }
}

const updateComponentCount = () => {
  // Simple heuristic: count DOM elements with Vue data attributes
  const vueElements = document.querySelectorAll('[data-v-]')
  componentCount.value = vueElements.length
}

onMounted(() => {
  if (isDev) {
    animationId = requestAnimationFrame(updateFPS)
    
    const interval = setInterval(() => {
      updateMemoryUsage()
      updateComponentCount()
    }, 1000)
    
    onUnmounted(() => {
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
      clearInterval(interval)
    })
  }
})
</script> 