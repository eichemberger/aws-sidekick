import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type Theme = 'light' | 'dark' | 'system'

export const useThemeStore = defineStore('theme', () => {
  // State
  const theme = ref<Theme>('system')
  const systemPrefersDark = ref(false)

  // Computed
  const isDark = computed(() => {
    if (theme.value === 'system') {
      return systemPrefersDark.value
    }
    return theme.value === 'dark'
  })

  const currentTheme = computed(() => {
    return isDark.value ? 'dark' : 'light'
  })

  // Actions
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    applyTheme()
  }

  const toggleTheme = () => {
    if (theme.value === 'light') {
      setTheme('dark')
    } else if (theme.value === 'dark') {
      setTheme('system')
    } else {
      setTheme('light')
    }
  }

  const applyTheme = () => {
    const root = document.documentElement
    
    if (isDark.value) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  const initializeTheme = () => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') as Theme
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      theme.value = savedTheme
    }

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = mediaQuery.matches

    const handleMediaChange = (e: MediaQueryListEvent) => {
      systemPrefersDark.value = e.matches
    }

    mediaQuery.addEventListener('change', handleMediaChange)

    // Apply initial theme
    applyTheme()

    // Watch for theme changes
    watch(isDark, applyTheme)

    // Cleanup function
    return () => {
      mediaQuery.removeEventListener('change', handleMediaChange)
    }
  }

  const getThemeIcon = (themeType: Theme) => {
    switch (themeType) {
      case 'light':
        return 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z'
      case 'dark':
        return 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z'
      case 'system':
        return 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
      default:
        return ''
    }
  }

  const getThemeLabel = (themeType: Theme) => {
    switch (themeType) {
      case 'light':
        return 'Light'
      case 'dark':
        return 'Dark'
      case 'system':
        return 'System'
      default:
        return ''
    }
  }

  return {
    // State
    theme,
    systemPrefersDark,
    
    // Computed
    isDark,
    currentTheme,
    
    // Actions
    setTheme,
    toggleTheme,
    initializeTheme,
    getThemeIcon,
    getThemeLabel
  }
}) 