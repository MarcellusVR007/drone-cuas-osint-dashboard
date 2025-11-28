import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchIncidents as apiFetchIncidents } from '../api/incidents'

export const useIncidentsStore = defineStore('incidents', () => {
  // State
  const incidents = ref([])
  const loading = ref(false)
  const error = ref(null)
  const total = ref(0)

  // Filter state
  const currentPage = ref(1)
  const pageSize = ref(50)
  const sortBy = ref('sighting_date')
  const sortOrder = ref('desc')

  // Getters
  const hasIncidents = computed(() => incidents.value.length > 0)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  // Actions
  async function loadIncidents(params = {}) {
    // Don't show loading if we already have data (prevents flash)
    if (incidents.value.length === 0) {
      loading.value = true
    }
    error.value = null

    try {
      const result = await apiFetchIncidents({
        limit: pageSize.value,
        skip: (currentPage.value - 1) * pageSize.value,
        order_by: sortOrder.value === 'desc' ? 'recent' : 'oldest',
        ...params
      })

      incidents.value = result.incidents || []
      total.value = result.total || 0
    } catch (err) {
      error.value = err.message
      console.error('Failed to load incidents:', err)
    } finally {
      loading.value = false
    }
  }

  function setSortBy(field) {
    if (sortBy.value === field) {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortBy.value = field
      sortOrder.value = 'desc'
    }
    loadIncidents()
  }

  function setPage(page) {
    currentPage.value = page
    loadIncidents()
  }

  return {
    // State
    incidents,
    loading,
    error,
    total,
    currentPage,
    pageSize,
    sortBy,
    sortOrder,
    // Getters
    hasIncidents,
    totalPages,
    // Actions
    loadIncidents,
    setSortBy,
    setPage
  }
})
