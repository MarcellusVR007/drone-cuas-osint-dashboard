<template>
  <div class="map-view">
    <div v-if="loading" class="loading">Loading map...</div>
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useIncidentsStore } from '../store/incidents'
import { useRouter } from 'vue-router'

const mapContainer = ref(null)
const loading = ref(true)
let map = null
const markers = []
const router = useRouter()
const incidentsStore = useIncidentsStore()

onMounted(async () => {
  // Initialize map first (faster perceived load)
  map = L.map(mapContainer.value).setView([51.5, 10], 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map)

  loading.value = false

  // Load incidents in background
  await incidentsStore.loadIncidents({ limit: 500 })

  // Add incident markers
  incidentsStore.incidents.forEach(incident => {
    if (incident.latitude && incident.longitude && incident.latitude !== 0) {
      const marker = L.circleMarker([incident.latitude, incident.longitude], {
        radius: 8,
        fillColor: '#dc3545',
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.7
      })

      marker.bindPopup(`
        <div style="color: #333;">
          <strong>${incident.title}</strong><br>
          ${incident.sighting_date}<br>
          ${incident.location_name || 'Unknown location'}<br>
          <a href="#" onclick="window.dispatchEvent(new CustomEvent('navigate-incident', {detail: ${incident.id}})); return false;">View details</a>
        </div>
      `)

      marker.on('click', () => {
        router.push(`/incident/${incident.id}`)
      })

      marker.addTo(map)
      markers.push(marker)
    }
  })
})

onUnmounted(() => {
  if (map) {
    map.remove()
  }
})
</script>

<style scoped>
.map-view {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}

.map-container {
  width: 100%;
  height: 100%;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #dc3545;
  font-size: 1.2rem;
  z-index: 1000;
}
</style>
