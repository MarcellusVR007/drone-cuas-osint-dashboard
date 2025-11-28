<template>
  <div class="incident-detail-view">
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading tactical intelligence for incident #{{ incidentId }}...</p>
      <p class="loading-subtext">Fetching data, imagery, and analysis...</p>
    </div>
    <iframe
      ref="iframeRef"
      :src="`http://127.0.0.1:8001/incident_detail.html?id=${incidentId}`"
      class="detail-iframe"
      :class="{ hidden: loading }"
      title="Incident Detail"
      @load="onIframeLoad"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const incidentId = ref(route.params.id)
const loading = ref(true)
const iframeRef = ref(null)

// Set a maximum loading time
let loadingTimeout = null

onMounted(() => {
  // Show iframe after 500ms to let it start loading
  setTimeout(() => {
    loading.value = false
  }, 500)

  // Cleanup timeout after 10 seconds max
  loadingTimeout = setTimeout(() => {
    if (loading.value) {
      console.log('Force showing iframe after timeout')
      loading.value = false
    }
  }, 10000)
})

function onIframeLoad(event) {
  // Clear timeout
  if (loadingTimeout) {
    clearTimeout(loadingTimeout)
    loadingTimeout = null
  }

  // Iframe is loaded
  loading.value = false

  try {
    const iframe = event.target
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document

    // Hide navbar (the duplicate menu)
    const navbar = iframeDoc.querySelector('.navbar')
    if (navbar) navbar.style.display = 'none'

    // Hide sidebar if present
    const sidebar = iframeDoc.querySelector('.sidebar')
    if (sidebar) sidebar.style.display = 'none'

    // Hide back button
    const backBtn = iframeDoc.querySelector('.back-btn')
    if (backBtn) backBtn.style.display = 'none'

    // Adjust container spacing
    const container = iframeDoc.querySelector('.container-fluid')
    if (container) {
      container.style.paddingTop = '0.5rem'
      container.style.marginTop = '0'
    }

    // Adjust body spacing
    const body = iframeDoc.querySelector('body')
    if (body) {
      body.style.paddingTop = '0'
      body.style.marginTop = '0'
    }
  } catch (e) {
    console.log('Could not access iframe content:', e.message)
  }
}
</script>

<style scoped>
.incident-detail-view {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #0f0f0f;
  z-index: 10;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #333;
  border-top-color: #dc3545;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  margin-top: 1rem;
  color: #dc3545;
  font-size: 1.1rem;
  font-weight: 600;
}

.loading-subtext {
  margin-top: 0.5rem !important;
  color: #999 !important;
  font-size: 0.9rem !important;
  font-weight: 400 !important;
}

.detail-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.detail-iframe.hidden {
  visibility: hidden;
}
</style>
