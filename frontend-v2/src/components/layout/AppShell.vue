<template>
  <div class="app-shell">
    <!-- Top Navigation -->
    <nav class="navbar">
      <div class="navbar-brand">
        <i class="fas fa-drone"></i> OSINT CUAS
      </div>
      <span class="navbar-subtitle">Counter-UAS Intelligence Dashboard</span>
    </nav>

    <!-- Main Container -->
    <div class="main-container">
      <!-- Sidebar -->
      <aside class="sidebar">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-item"
          :class="{ active: $route.path === item.path }"
        >
          <i :class="item.icon"></i> {{ item.label }}
        </router-link>

        <!-- Intelligence Section -->
        <div class="sidebar-section-title">Intelligence</div>
        <router-link
          v-for="item in intelligenceItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-item"
          :class="{ active: $route.path === item.path }"
        >
          <i :class="item.icon"></i> {{ item.label }}
        </router-link>

        <!-- Forensics Section -->
        <div class="sidebar-section-title">Forensics</div>
        <router-link
          v-for="item in forensicsItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-item"
          :class="{ active: $route.path === item.path }"
        >
          <i :class="item.icon"></i> {{ item.label }}
        </router-link>
      </aside>

      <!-- Main Content Area -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
const menuItems = [
  { path: '/', label: 'Dashboard', icon: 'fas fa-chart-line' },
  { path: '/incidents-map', label: 'Incidents Map', icon: 'fas fa-map' },
  { path: '/patterns', label: 'Patterns', icon: 'fas fa-network-wired' }
]

const intelligenceItems = [
  { path: '/intel-hub', label: 'Intel Hub', icon: 'fas fa-shield-alt' },
  { path: '/telegram', label: 'Telegram', icon: 'fab fa-telegram' },
  { path: '/forums', label: 'Forums', icon: 'fas fa-comments' }
]

const forensicsItems = [
  { path: '/phone-intel', label: 'Phone Intelligence', icon: 'fas fa-phone' }
]
</script>

<style scoped>
.app-shell {
  width: 100vw;
  height: 100vh;
  background: #0f0f0f;
  color: #e0e0e0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.navbar {
  background: #1a1a1a;
  border-bottom: 2px solid #dc3545;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 6px rgba(220, 53, 69, 0.1);
}

.navbar-brand {
  font-weight: 700;
  font-size: 1.3rem;
  color: #dc3545;
  letter-spacing: 1px;
}

.navbar-subtitle {
  color: #dc3545;
  font-size: 0.9rem;
  margin-left: auto;
}

.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 250px;
  background: #2d2d2d;
  border-right: 1px solid rgba(220, 53, 69, 0.2);
  padding: 1rem 0;
  overflow-y: auto;
  flex-shrink: 0;
}

.sidebar-item {
  display: block;
  padding: 0.75rem 1.5rem;
  color: #e0e0e0;
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.sidebar-item:hover {
  background: rgba(220, 53, 69, 0.1);
  border-left-color: #dc3545;
}

.sidebar-item.active {
  background: rgba(220, 53, 69, 0.2);
  border-left-color: #dc3545;
  color: #dc3545;
  font-weight: 600;
}

.sidebar-item i {
  width: 20px;
  margin-right: 0.5rem;
}

.sidebar-section-title {
  padding: 1rem 1.5rem 0.5rem;
  margin-top: 1rem;
  font-size: 0.7rem;
  color: #666;
  border-top: 1px solid #333;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 1px;
}

.content {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  background: #0f0f0f;
  position: relative;
}
</style>
