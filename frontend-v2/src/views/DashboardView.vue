<template>
  <div class="dashboard-view">
    <div class="page-header">
      <h1>Drone OSINT Dashboard ({{ total }} incidents)</h1>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> Loading incidents...
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
    </div>

    <!-- Incidents Table -->
    <div v-else-if="hasIncidents" class="table-container">
      <table class="incidents-table">
        <thead>
          <tr>
            <th @click="setSortBy('id')" class="sortable">
              # <i :class="getSortIcon('id')"></i>
            </th>
            <th @click="setSortBy('sighting_date')" class="sortable">
              Date <i :class="getSortIcon('sighting_date')"></i>
            </th>
            <th @click="setSortBy('title')" class="sortable">
              Title <i :class="getSortIcon('title')"></i>
            </th>
            <th @click="setSortBy('location_name')" class="sortable">
              Location <i :class="getSortIcon('location_name')"></i>
            </th>
            <th @click="setSortBy('country')" class="sortable">
              Country <i :class="getSortIcon('country')"></i>
            </th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="incident in incidents" :key="incident.id" class="incident-row">
            <td class="incident-number">#{{ formatIncidentNumber(incident.id) }}</td>
            <td>{{ formatDate(incident.sighting_date) }}</td>
            <td class="title-cell">{{ incident.title }}</td>
            <td>{{ incident.location_name || 'Unknown' }}</td>
            <td>{{ incident.country || '-' }}</td>
            <td class="action-cell">
              <button @click="goToDetail(incident.id)" class="detail-btn">
                <i class="fas fa-arrow-right"></i> Detail
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="pagination">
        <button
          @click="setPage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="pagination-btn"
        >
          <i class="fas fa-chevron-left"></i> Previous
        </button>

        <span class="pagination-info">
          Page {{ currentPage }} of {{ totalPages }} ({{ total }} incidents)
        </span>

        <button
          @click="setPage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="pagination-btn"
        >
          Next <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <i class="fas fa-inbox"></i>
      <p>No incidents found</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useIncidentsStore } from '../store/incidents'

const router = useRouter()
const incidentsStore = useIncidentsStore()
const { incidents, loading, error, total, currentPage, totalPages, hasIncidents, sortBy, sortOrder } = storeToRefs(incidentsStore)
const { loadIncidents, setSortBy, setPage } = incidentsStore

// Load incidents on mount
onMounted(() => {
  loadIncidents()
})

// Format incident number with leading zeros
function formatIncidentNumber(id) {
  return String(id).padStart(3, '0')
}

// Format date from YYYY-MM-DD to DD-MM-YYYY
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const [year, month, day] = dateStr.split('-')
  return `${day}-${month}-${year}`
}

// Get sort icon for column
function getSortIcon(field) {
  if (sortBy.value !== field) {
    return 'fas fa-sort'
  }
  return sortOrder.value === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down'
}

// Navigate to incident detail
function goToDetail(id) {
  router.push(`/incident/${id}`)
}
</script>

<style scoped>
.dashboard-view {
  max-width: 1600px;
  margin: 0;
  padding: 2rem;
  min-height: 100%;
  box-sizing: border-box;
  width: 100%;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  color: #dc3545;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #999;
}

.loading-state i {
  font-size: 2rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.error-state {
  color: #dc3545;
}

.error-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.table-container {
  background: #1a1a1a;
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.incidents-table {
  width: 100%;
  border-collapse: collapse;
}

.incidents-table thead {
  background: #2d2d2d;
  border-bottom: 2px solid #dc3545;
}

.incidents-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #dc3545;
  text-transform: uppercase;
  font-size: 0.85rem;
  letter-spacing: 0.5px;
}

.incidents-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.incidents-table th.sortable:hover {
  background: rgba(220, 53, 69, 0.1);
}

.incidents-table th i {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  opacity: 0.6;
}

.incidents-table tbody tr {
  border-bottom: 1px solid #333;
  transition: background 0.2s;
}

.incidents-table tbody tr:hover {
  background: rgba(220, 53, 69, 0.05);
}

.incidents-table td {
  padding: 1rem;
  color: #e0e0e0;
}

.incident-number {
  font-weight: 700;
  color: #dc3545;
  font-family: 'Courier New', monospace;
}

.title-cell {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-cell {
  text-align: right;
  padding-right: 1.5rem !important;
}

.source-badge {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
}

.detail-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-btn:hover {
  background: #c82333;
  transform: translateX(2px);
}

.detail-btn i {
  font-size: 0.75rem;
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: #2d2d2d;
  border-top: 1px solid #333;
}

.pagination-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  font-weight: 600;
}

.pagination-btn:hover:not(:disabled) {
  background: #c82333;
}

.pagination-btn:disabled {
  background: #555;
  cursor: not-allowed;
  opacity: 0.5;
}

.pagination-info {
  color: #999;
  font-size: 0.9rem;
}
</style>
