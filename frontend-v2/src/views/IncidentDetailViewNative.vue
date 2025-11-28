<template>
  <div class="incident-detail-native">
    <div v-if="loading" class="loading">
      <i class="fas fa-spinner fa-spin"></i> Loading incident...
    </div>

    <div v-else-if="error" class="error">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
    </div>

    <div v-else-if="incident" class="detail-content">
      <!-- Header -->
      <div class="detail-header">
        <div class="incident-number">#{{ formatIncidentNumber(incident.id) }}</div>
        <h1>{{ incident.title }}</h1>
        <div class="meta-row">
          <span class="meta-item">
            <i class="fas fa-calendar"></i> {{ formatDate(incident.sighting_date) }}
          </span>
          <span class="meta-item" v-if="incident.sighting_time">
            <i class="fas fa-clock"></i> {{ incident.sighting_time }}
          </span>
          <span class="meta-item">
            <i class="fas fa-map-marker-alt"></i> {{ locationName }}
          </span>
          <span class="meta-item">
            <i class="fas fa-flag"></i> {{ countryName }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <div class="section" v-if="incident.description">
        <h2><i class="fas fa-info-circle"></i> Description</h2>
        <div v-html="incident.description" class="description"></div>
      </div>

      <!-- Technical Details -->
      <div class="section">
        <h2><i class="fas fa-cogs"></i> Technical Details</h2>
        <div class="details-grid">
          <div class="detail-item">
            <span class="label">Coordinates:</span>
            <span class="value">{{ incident.latitude }}, {{ incident.longitude }}</span>
          </div>
          <div class="detail-item" v-if="incident.altitude_m">
            <span class="label">Altitude:</span>
            <span class="value">{{ incident.altitude_m }}m</span>
          </div>
          <div class="detail-item" v-if="incident.duration_minutes">
            <span class="label">Duration:</span>
            <span class="value">{{ incident.duration_minutes }} minutes</span>
          </div>
          <div class="detail-item">
            <span class="label">Confidence:</span>
            <span class="value">{{ (incident.confidence_score * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </div>

      <!-- Drone Information -->
      <div class="section" v-if="incident.drone_description || incident.drone_characteristics">
        <h2><i class="fas fa-drone"></i> Drone Information</h2>
        <div class="details-grid">
          <div class="detail-item" v-if="incident.drone_type_name">
            <span class="label">Type:</span>
            <span class="value">{{ incident.drone_type_name }}</span>
          </div>
          <div class="detail-item" v-if="incident.drone_description">
            <span class="label">Description:</span>
            <span class="value">{{ incident.drone_description }}</span>
          </div>
          <div class="detail-item" v-if="incident.drone_characteristics">
            <span class="label">Characteristics:</span>
            <span class="value">{{ incident.drone_characteristics }}</span>
          </div>
        </div>
      </div>

      <!-- Source Information -->
      <div class="section">
        <h2><i class="fas fa-newspaper"></i> Source</h2>
        <div class="details-grid">
          <div class="detail-item">
            <span class="label">Source:</span>
            <span class="value">{{ incident.display_source || incident.source }}</span>
          </div>
          <div class="detail-item" v-if="incident.identified_by">
            <span class="label">Identified by:</span>
            <span class="value">{{ incident.identified_by }}</span>
          </div>
          <div class="detail-item" v-if="incident.source_url">
            <span class="label">URL:</span>
            <span class="value">
              <a :href="incident.source_url" target="_blank" class="source-link">
                View Source <i class="fas fa-external-link-alt"></i>
              </a>
            </span>
          </div>
        </div>
      </div>

      <!-- Assessment -->
      <div class="section" v-if="incident.suspected_operator || incident.purpose_assessment">
        <h2><i class="fas fa-user-secret"></i> Assessment</h2>
        <div class="details-grid">
          <div class="detail-item" v-if="incident.suspected_operator">
            <span class="label">Suspected Operator:</span>
            <span class="value">{{ incident.suspected_operator }}</span>
          </div>
          <div class="detail-item" v-if="incident.purpose_assessment">
            <span class="label">Purpose:</span>
            <span class="value">{{ incident.purpose_assessment }}</span>
          </div>
        </div>
      </div>

      <!-- Multi-Source Intelligence -->
      <div class="section" v-if="secondarySources && secondarySources.length > 0">
        <h2><i class="fas fa-newspaper"></i> Multi-Source Intelligence</h2>
        <p class="section-intro">
          This incident has been corroborated by {{ secondarySources.length }} additional sources,
          providing cross-validated intelligence.
        </p>
        <div class="sources-grid">
          <div v-for="(source, idx) in secondarySources" :key="idx" class="source-card">
            <div class="source-header">
              <span class="source-name">{{ source.name }}</span>
              <span class="credibility-badge" :class="getCredibilityClass(source.credibility)">
                {{ getCredibilityLabel(source.credibility) }}
              </span>
            </div>
            <a :href="source.url" target="_blank" class="source-url">
              <i class="fas fa-external-link-alt"></i> View Source
            </a>
          </div>
        </div>
      </div>

      <!-- Location Map -->
      <div class="section">
        <h2><i class="fas fa-map-marked-alt"></i> Geolocation</h2>
        <div class="map-container" ref="mapContainer"></div>
        <div class="details-grid" style="margin-top: 1rem;">
          <div class="detail-item">
            <span class="label">Coordinates:</span>
            <span class="value">{{ incident.latitude?.toFixed(4) }}, {{ incident.longitude?.toFixed(4) }}</span>
          </div>
          <div class="detail-item" v-if="restrictedArea">
            <span class="label">Restricted Area:</span>
            <span class="value">{{ restrictedArea.name }}</span>
          </div>
          <div class="detail-item" v-if="incident.distance_to_restricted_m">
            <span class="label">Distance to Restricted Area:</span>
            <span class="value">{{ incident.distance_to_restricted_m }}m</span>
          </div>
        </div>
      </div>

      <!-- Additional Details -->
      <div class="section" v-if="incident.details">
        <h2><i class="fas fa-file-alt"></i> Additional Details</h2>
        <div class="details-text" v-html="incident.details"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const route = useRoute()
const incidentId = route.params.id

const incident = ref(null)
const loading = ref(true)
const error = ref(null)
const restrictedArea = ref(null)
const mapContainer = ref(null)
let map = null

const locationName = computed(() => {
  return incident.value?.location_name || restrictedArea.value?.name || 'Unknown location'
})

const secondarySources = computed(() => {
  try {
    if (incident.value?.secondary_sources) {
      const sources = typeof incident.value.secondary_sources === 'string'
        ? JSON.parse(incident.value.secondary_sources)
        : incident.value.secondary_sources
      return Array.isArray(sources) ? sources : []
    }
  } catch (e) {
    console.error('Error parsing secondary sources:', e)
  }
  return []
})

const countryName = computed(() => {
  const code = incident.value?.country
  const countryMap = {
    'NL': 'Netherlands',
    'BE': 'Belgium',
    'DE': 'Germany',
    'FR': 'France',
    'UK': 'United Kingdom',
    'EE': 'Estonia',
    'LV': 'Latvia',
    'LT': 'Lithuania',
    'PL': 'Poland',
    'IT': 'Italy',
    'ES': 'Spain'
  }
  return countryMap[code] || code || 'Unknown'
})

function formatIncidentNumber(id) {
  return String(id).padStart(3, '0')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const [year, month, day] = dateStr.split('-')
  return `${day}-${month}-${year}`
}

function getCredibilityClass(score) {
  if (score >= 8) return 'credibility-high'
  if (score >= 6) return 'credibility-medium'
  return 'credibility-low'
}

function getCredibilityLabel(score) {
  if (score >= 8) return 'High Credibility'
  if (score >= 6) return 'Medium Credibility'
  return 'Low Credibility'
}

function initMap() {
  if (!mapContainer.value || !incident.value) return

  map = L.map(mapContainer.value).setView(
    [incident.value.latitude, incident.value.longitude],
    13
  )

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map)

  // Add incident marker
  L.marker([incident.value.latitude, incident.value.longitude], {
    icon: L.divIcon({
      className: 'custom-marker',
      html: '<div style="background: #dc3545; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white;"></div>'
    })
  }).addTo(map).bindPopup(`
    <strong>Incident #${formatIncidentNumber(incident.value.id)}</strong><br>
    ${incident.value.title}
  `)
}

onMounted(async () => {
  try {
    // Fetch incident details
    const response = await fetch(`http://127.0.0.1:8001/api/incidents/${incidentId}`)
    if (!response.ok) throw new Error('Failed to load incident')

    const data = await response.json()
    incident.value = data

    // Fetch restricted area if available
    if (data.restricted_area_id) {
      try {
        const areaResponse = await fetch(`http://127.0.0.1:8001/api/restricted-areas/${data.restricted_area_id}`)
        if (areaResponse.ok) {
          restrictedArea.value = await areaResponse.json()
        }
      } catch (e) {
        console.log('Could not fetch restricted area:', e)
      }
    }

    // Initialize map after data is loaded
    setTimeout(() => initMap(), 100)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.incident-detail-native {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
}

.loading, .error {
  text-align: center;
  padding: 4rem 2rem;
  color: #999;
}

.loading i {
  font-size: 2rem;
  color: #dc3545;
  margin-bottom: 1rem;
}

.error {
  color: #dc3545;
}

.detail-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.detail-header {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 2px solid #dc3545;
}

.incident-number {
  display: inline-block;
  background: #dc3545;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.detail-header h1 {
  font-size: 2rem;
  color: #dc3545;
  margin: 1rem 0;
  line-height: 1.3;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-top: 1rem;
}

.meta-item {
  color: #999;
  font-size: 0.95rem;
}

.meta-item i {
  color: #dc3545;
  margin-right: 0.5rem;
}

.section {
  background: #1a1a1a;
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.section h2 {
  color: #dc3545;
  font-size: 1.3rem;
  margin: 0 0 1.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section h2 i {
  font-size: 1.1rem;
}

.description {
  color: #e0e0e0;
  line-height: 1.6;
}

.description a {
  color: #dc3545;
  text-decoration: none;
}

.description a:hover {
  text-decoration: underline;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.label {
  color: #999;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.value {
  color: #e0e0e0;
  font-size: 1rem;
}

.source-link {
  color: #dc3545;
  text-decoration: none;
  transition: color 0.2s;
}

.source-link:hover {
  color: #ff4757;
}

.source-link i {
  font-size: 0.85rem;
  margin-left: 0.25rem;
}

.section-intro {
  color: #999;
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.source-card {
  background: #0f0f0f;
  border: 1px solid rgba(220, 53, 69, 0.2);
  border-radius: 6px;
  padding: 1rem;
  transition: all 0.2s;
}

.source-card:hover {
  border-color: rgba(220, 53, 69, 0.5);
  transform: translateY(-2px);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.source-name {
  font-weight: 600;
  color: #e0e0e0;
  font-size: 0.95rem;
}

.credibility-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.credibility-high {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.credibility-medium {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.credibility-low {
  background: rgba(220, 53, 69, 0.2);
  color: #dc3545;
}

.source-url {
  color: #dc3545;
  text-decoration: none;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.source-url:hover {
  color: #ff4757;
}

.map-container {
  width: 100%;
  height: 400px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(220, 53, 69, 0.3);
}

.details-text {
  color: #e0e0e0;
  line-height: 1.8;
  font-size: 0.95rem;
}

.details-text a {
  color: #dc3545;
  text-decoration: none;
}

.details-text a:hover {
  text-decoration: underline;
}
</style>
