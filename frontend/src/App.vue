<template>
  <div class="app">
    <Navbar />
    <div class="main-layout">
      <Sidebar />
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import Navbar from './components/layout/Navbar.vue'
import Sidebar from './components/layout/Sidebar.vue'
</script>

<style scoped>
.app { min-height: 100vh; background: #f8fafc; }
.main-layout { 
  display: flex; 
  padding-top: 64px; 
}
.content-area { 
  flex: 1; 
  padding: 24px; 
  margin-left: 260px;   /* ← Important: offset for fixed sidebar */
}
</style>