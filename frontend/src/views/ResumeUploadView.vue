<template>
  <div>
    <h1>📤 Upload Resumes</h1>

    <div class="upload-card">
      <input
        type="file"
        multiple
        accept=".pdf,.docx"
        @change="handleFileSelect"
        ref="fileInput"
        style="display: none"
      />
      
      <button @click="triggerFileInput" class="upload-btn">
        Choose Resume Files (PDF / DOCX)
      </button>

      <div v-if="selectedFiles.length" class="selected-files">
        <h4>Selected {{ selectedFiles.length }} file(s):</h4>
        <ul>
          <li v-for="(file, index) in selectedFiles" :key="index">{{ file.name }}</li>
        </ul>
      </div>

      <button 
        v-if="selectedFiles.length" 
        @click="uploadResumes"
        :disabled="uploading"
        class="submit-btn"
      >
        {{ uploading ? 'Uploading & Processing...' : `Upload ${selectedFiles.length} Resume(s)` }}
      </button>
    </div>

    <!-- Status Messages -->
    <div v-if="uploadResults.length" class="results-section">
      <h2>Processing Results</h2>
      <div class="result-grid">
        <div v-for="(result, i) in uploadResults" :key="i" class="result-card">
          <h4>✅ {{ result.name }}</h4>
          <p><strong>Total Experience:</strong> {{ result.experience || 0 }} years</p>
          <p><strong>Education:</strong> {{ result.education || 'Not mentioned' }}</p>
          
          <div class="skills-box">
            <strong>Skills with Experience:</strong>
            <ul v-if="result.skill_experience && result.skill_experience.length">
              <li v-for="(item, idx) in result.skill_experience" :key="idx">
                <strong>{{ item.skill }}</strong> — {{ item.experience }} years
              </li>
            </ul>
            <p v-else>Skills: {{ result.skills?.join(', ') || 'No skills extracted' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'

const fileInput = ref<null | HTMLInputElement>(null)
const selectedFiles = ref<File[]>([])
const uploading = ref(false)
const uploadResults = ref<any[]>([])

const API_BASE = 'http://localhost:8000/api'

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    selectedFiles.value = Array.from(input.files)
  }
}

const uploadResumes = async () => {
  if (selectedFiles.value.length === 0) return

  uploading.value = true
  uploadResults.value = []

  for (const file of selectedFiles.value) {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/resume/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      uploadResults.value.push({ name: file.name, ...response.data })
    } catch (error: any) {
      uploadResults.value.push({
        name: file.name,
        error: error.response?.data?.detail || 'Failed to upload'
      })
    }
  }

  uploading.value = false
  selectedFiles.value = []   // Clear after upload
}
</script>

<style scoped>
/* Add your existing styles + */
.upload-card, .result-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 24px;
}

.submit-btn {
  background: #10b981;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

.skills-box ul {
  margin-top: 8px;
  padding-left: 20px;
}
</style>