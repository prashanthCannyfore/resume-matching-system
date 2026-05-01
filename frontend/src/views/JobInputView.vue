<template>
  <div class="job-page">
    <h1>✍️ Job Description Input</h1>

    <div class="job-form-card">
      <div class="form-group">
        <label>Job Title</label>
        <input
          v-model="jobData.title"
          type="text"
          placeholder="e.g. Senior React Developer"
          class="input-field"
        />
      </div>

      <div class="form-group">
        <label>Job Description</label>
        <textarea
          v-model="jobData.description_text"
          rows="14"
          placeholder="Paste the full job description here..."
          class="textarea-field"
        ></textarea>
      </div>

      <button 
        @click="submitJob" 
        :disabled="loading || !jobData.title || !jobData.description_text"
        class="submit-btn"
      >
        {{ loading ? 'Saving Job...' : 'Save Job Description' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

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
    const response = await axios.post(`${API_BASE}/jobs/`, jobData.value)
    alert(`✅ Job created successfully! ID: ${response.data.id}`)
    // Clear form after success
    jobData.value.title = ''
    jobData.value.description_text = ''
  } catch (error: any) {
    console.error(error)
    alert("❌ Failed to create job. Check console for details.")
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
}

.submit-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}
</style>