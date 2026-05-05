<template>
  <div class="dashboard">
    <h1>📊 Dashboard</h1>

    <div class="welcome">
      <h2>Welcome back to Resume Matching System</h2>
      <p>Manage your resumes and find the best candidates quickly.</p>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <router-link to="/upload-resume" class="action-card">
        <span class="icon">📤</span>
        <h3>Upload Resumes</h3>
        <p>Add new candidate resumes</p>
      </router-link>

      <router-link to="/job-input" class="action-card">
        <span class="icon">✍️</span>
        <h3>New Job Description</h3>
        <p>Create job and find matches</p>
      </router-link>
    </div>

    <!-- Recent Jobs -->
    <div class="recent-jobs">
      <div class="section-header">
        <h2>Recent Jobs</h2>
        <button @click="fetchRecentJobs" class="refresh-btn">↻ Refresh</button>
      </div>

      <div v-if="loading" class="loading">Loading recent jobs...</div>

      <div v-else-if="recentJobs.length === 0" class="empty-state">
        No jobs created yet. Create your first job from the "New Job Description" section.
      </div>

      <div v-else class="jobs-grid">
        <div 
          v-for="job in recentJobs" 
          :key="job.id" 
          class="job-card"
          @click="viewMatches(job.id)"
        >
          <h3>{{ job.title }}</h3>
          <p class="date">Created: {{ formatDate(job.created_at) }}</p>
          
          <div class="stats">
            <span v-if="job.required_skills && job.required_skills.length">
              {{ job.required_skills.length }} Skills
            </span>
            <span v-if="job.min_experience">
              Min Exp: {{ job.min_experience }} years
            </span>
          </div>

          <button class="match-btn" @click.stop="viewMatches(job.id)">
            View Matching Candidates →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const recentJobs = ref<any[]>([])
const loading = ref(false)

const API_BASE = 'http://localhost:8000/api'

const fetchRecentJobs = async () => {
  loading.value = true
  try {
    // For now, we fetch from jobs endpoint. 
    // You can improve this later by adding a dedicated GET /jobs endpoint
    const res = await axios.get(`${API_BASE}/jobs`)  // We'll add this later if needed
    recentJobs.value = res.data.slice(0, 6) // Show latest 6 jobs
  } catch (err) {
    console.error("Failed to fetch jobs", err)
    // Fallback: show empty for now
    recentJobs.value = []
  } finally {
    loading.value = false
  }
}

const viewMatches = (jobId: number) => {
  router.push(`/matching/${jobId}`)
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Load recent jobs when dashboard mounts
onMounted(() => {
  fetchRecentJobs()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome {
  margin-bottom: 40px;
}

.welcome h2 {
  color: #1e2937;
  margin-bottom: 8px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 50px;
}

.action-card {
  background: white;
  padding: 28px;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0,0,0,0.12);
}

.action-card .icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.job-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: all 0.2s;
}

.job-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.15);
}

.job-card h3 {
  margin-bottom: 8px;
  color: #1e2937;
}

.date {
  color: #64748b;
  font-size: 0.95rem;
  margin-bottom: 16px;
}

.stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  color: #475569;
  font-size: 0.95rem;
}

.match-btn {
  width: 100%;
  padding: 10px;
  background: #1e40af;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
}

.match-btn:hover {
  background: #1e3a8a;
}

.loading, .empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}
</style>