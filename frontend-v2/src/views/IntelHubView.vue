<template>
  <div class="intel-hub-view">
    <iframe
      src="http://127.0.0.1:8001/intelligence.html"
      class="intel-iframe"
      title="Intel Hub"
      @load="hideIframeNavbar"
    />
  </div>
</template>

<script setup>
function hideIframeNavbar(event) {
  try {
    const iframe = event.target
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document
    const navbar = iframeDoc.querySelector('.navbar')
    if (navbar) {
      navbar.style.display = 'none'
    }
    const container = iframeDoc.querySelector('.container-fluid')
    if (container) {
      container.style.marginTop = '0'
      container.style.paddingTop = '0.5rem'
    }
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
.intel-hub-view {
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

.intel-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>
