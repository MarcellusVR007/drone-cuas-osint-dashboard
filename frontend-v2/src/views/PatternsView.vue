<template>
  <div class="patterns-view">
    <iframe
      src="http://127.0.0.1:8001/patterns.html"
      class="patterns-iframe"
      title="Patterns Analysis"
      @load="hideIframeNavbar"
    />
  </div>
</template>

<script setup>
function hideIframeNavbar(event) {
  try {
    const iframe = event.target
    const iframeDoc = iframe.contentDocument || iframe.contentWindow.document

    // Hide the navbar in the embedded page
    const navbar = iframeDoc.querySelector('.navbar')
    if (navbar) {
      navbar.style.display = 'none'
    }

    // Also hide any "back to home" links
    const container = iframeDoc.querySelector('.container-fluid')
    if (container) {
      container.style.marginTop = '0'
    }
  } catch (e) {
    // Cross-origin restrictions might prevent this
    console.log('Could not access iframe content:', e.message)
  }
}
</script>

<style scoped>
.patterns-view {
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

.patterns-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>
