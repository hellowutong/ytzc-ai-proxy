import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const theme = ref(localStorage.getItem('theme') || 'light')
  const sidebarCollapsed = ref(false)
  const isLoading = ref(false)

  const isDark = computed(() => theme.value === 'dark')

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    document.documentElement.className = `theme-${theme.value}`
  }

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem('theme', theme.value)
    document.documentElement.className = `theme-${theme.value}`
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(loading) {
    isLoading.value = loading
  }

  return {
    theme,
    sidebarCollapsed,
    isLoading,
    isDark,
    toggleTheme,
    setTheme,
    toggleSidebar,
    setLoading
  }
})
