<template>
  <nav class="navbar">
    <div class="brand">
      <h1>RMS</h1>
      <span>Resume Matching System</span>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 64px;
  background: #1e2937;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 24px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand h1 {
  margin: 0;
  font-size: 1.8rem;
  color: #60a5fa;
}
</style>