<template>
  <div class="relative">
    <!-- Theme Toggle Button -->
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm"
      :class="[
        isDark 
          ? 'text-gray-300 hover:text-white' 
          : 'text-gray-600 hover:text-gray-900'
      ]"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path 
          stroke-linecap="round" 
          stroke-linejoin="round" 
          stroke-width="2" 
          :d="getThemeIcon(theme)"
        />
      </svg>
      <span class="hidden sm:inline">{{ getThemeLabel(theme) }}</span>
      <svg 
        class="w-3 h-3 transition-transform duration-200" 
        :class="{ 'rotate-180': isOpen }"
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Theme Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 bottom-full mb-2 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50"
      >
        <button
          v-for="themeOption in themeOptions"
          :key="themeOption"
          @click="selectTheme(themeOption)"
          class="w-full flex items-center gap-3 px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
          :class="[
            theme === themeOption
              ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-700 dark:text-gray-300'
          ]"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2" 
              :d="getThemeIcon(themeOption)"
            />
          </svg>
          {{ getThemeLabel(themeOption) }}
          <svg 
            v-if="theme === themeOption"
            class="w-3 h-3 ml-auto text-blue-600 dark:text-blue-400" 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path 
              fill-rule="evenodd" 
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" 
              clip-rule="evenodd" 
            />
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useThemeStore, type Theme } from '@/stores/theme'

const themeStore = useThemeStore()
const { theme, isDark, setTheme, getThemeIcon, getThemeLabel } = themeStore

const isOpen = ref(false)
const themeOptions: Theme[] = ['light', 'dark', 'system']

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectTheme = (newTheme: Theme) => {
  setTheme(newTheme)
  isOpen.value = false
}

// Close dropdown when clicking outside
const handleClickOutside = (event: Event) => {
  const target = event.target as Element
  if (!target.closest('.relative')) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script> 