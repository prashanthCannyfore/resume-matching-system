<template>
  <div class="job-page">
    <h1>✍️ Job Description Input</h1>

    <div class="job-form-card">
      <div class="form-group">
        <label>Job Title <span class="required">*</span></label>
        <input
          v-model="jobData.title"
          type="text"
          placeholder="e.g. Senior React Developer"
          class="input-field"
        />
      </div>

      <div class="form-group">
        <label>Job Description <span class="required">*</span></label>
        <textarea
          v-model="jobData.description_text"
          rows="15"
          placeholder="Paste the full job description here..."
          class="textarea-field"
        ></textarea>
      </div>

      <button 
        @click="submitJob" 
        :disabled="loading || !jobData.title.trim() || !jobData.description_text.trim()"
        class="submit-btn"
      >
        {{ loading ? 'Saving Job & Finding Best Candidates...' : 'Save Job & Find Matching Candidates' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const jobData = ref({
  title: '',
  description_text: ''
})

const loading = ref(false)
const API_BASE = 'http://localhost:8000/api'

const submitJob = async () => {
  if (!jobData.value.title.trim() || !jobData.value.description_text.trim()) {
    alert("Please fill both Job Title and Description")
    return
  }

  loading.value = true

  try {
    // Step 1: Create Job
    const jobRes = await axios.post(`${API_BASE}/jobs/`, jobData.value)
    const jobId = jobRes.data.id

    alert(`✅ Job created successfully! ID: ${jobId}\n\nFinding best matching candidates...`)

    // Step 2: Redirect to Matching Page with Job ID
    router.push(`/matching/${jobId}`)

    // Optional: Clear form
    jobData.value.title = ''
    jobData.value.description_text = ''

  } catch (error: any) {
    console.error(error)
    alert("❌ Failed to create job. Please check console for details.")
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.job-page h1 {
  margin-bottom: 24px;
  color: #1e2937;
}

.job-form-card {
  background: white;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
  max-width: 800px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
}

.required {
  color: #ef4444;
}

.input-field, .textarea-field {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 16px;
}

.textarea-field {
  resize: vertical;
  font-family: inherit;
}

.submit-btn {
  background: #10b981;
  color: white;
  padding: 14px 32px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  width: 100%;
}

.submit-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>