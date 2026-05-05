<template>
  <aside class="sidebar">
    <div class="menu-title">Navigation</div>
    
    <router-link to="/" class="menu-item">
      📊 Dashboard
    </router-link>
    <router-link to="/upload-resume" class="menu-item">
      📤 Upload Resumes
    </router-link>
    <router-link to="/job-input" class="menu-item">
      ✍️ Job Description
    </router-link>
  </aside>
</template>

<script setup lang="ts">
// Empty - router-link handles everything
</script>

<style scoped>
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e2e8f0;
  padding: 24px 12px;
  min-height: calc(100vh - 64px);
  position: fixed;
  left: 0;
  top: 64px;
  z-index: 900;           /* Important */
  overflow-y: auto;
}

.menu-title {
  font-weight: 600;
  color: #64748b;
  padding: 8px 16px 12px;
  font-size: 0.85rem;
  text-transform: uppercase;
}

.menu-item {
  display: block;
  padding: 14px 16px;
  margin: 4px 0;
  border-radius: 8px;
  color: #334155;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s ease;
  cursor: pointer;        /* Explicit cursor */
}

.menu-item:hover {
  background: #f0f9ff;
  color: #1e40af;
}

.menu-item.router-link-active {
  background: #dbeafe;
  color: #1e40af;
  font-weight: 600;
}
</style>