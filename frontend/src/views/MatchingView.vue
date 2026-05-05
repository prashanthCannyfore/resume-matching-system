<template>
  <div class="matching-page">
    <h1>🎯 Candidate Matching Results</h1>

    <div v-if="matchStore.currentJob" class="job-header">
      <h2>{{ matchStore.currentJob.job_title }}</h2>
      <p class="total">Total Candidates: <strong>{{ matchStore.matches.length }}</strong></p>
    </div>

    <!-- Controls -->
    <div class="controls-bar">
      <div class="sort-controls">
        <label>Sort By:</label>
        <button 
          :class="{ active: matchStore.sortBy === 'score' }"
          @click="matchStore.setSortBy('score')"
        >Match Score</button>
        <button 
          :class="{ active: matchStore.sortBy === 'experience' }"
          @click="matchStore.setSortBy('experience')"
        >Experience</button>
      </div>

      <div class="filter-controls">
        <label>Min Score: {{ Math.round(matchStore.filterMinScore * 100) }}%</label>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.05"
          v-model="matchStore.filterMinScore"
        />
      </div>
    </div>

    <!-- States -->
    <div v-if="matchStore.loading" class="loading-state">
      <p>🔍 Finding best matching candidates...</p>
    </div>

    <div v-else-if="matchStore.error" class="error-state">
      {{ matchStore.error }}
    </div>

    <!-- Candidate Cards -->
    <div v-else class="candidates-grid">
      <div 
        v-for="(candidate, index) in matchStore.filteredAndSortedMatches" 
        :key="index"
        class="candidate-card"
      >
        <div class="rank-badge">#{{ index + 1 }}</div>

        <h3>{{ candidate.name }}</h3>
        
        <div class="match-score">
          Match Score: <span class="score-value">{{ (candidate.score * 100).toFixed(1) }}%</span>
        </div>

        <p><strong>Experience:</strong> {{ candidate.experience_years || 0 }} years</p>

        <!-- AI Insights -->
        <div class="insights">
          <h4>🤖 AI Recruiter Insight</h4>
          <p class="summary">{{ candidate.insight?.summary }}</p>

          <div class="detail-section">
            <strong>Strengths</strong>
            <ul>
              <li v-for="(str, i) in candidate.insight?.strengths" :key="i">✓ {{ str }}</li>
            </ul>
          </div>

          <div class="detail-section" v-if="candidate.insight?.weaknesses?.length">
            <strong>Weaknesses</strong>
            <ul>
              <li v-for="(item, i) in candidate.insight?.weaknesses" :key="i">⚠ {{ item }}</li>
            </ul>
          </div>

          <div class="detail-section" v-if="candidate.insight?.skill_gaps?.length">
            <strong>Skill Gaps</strong>
            <ul>
              <li v-for="(gap, i) in candidate.insight?.skill_gaps" :key="i">→ {{ gap }}</li>
            </ul>
          </div>

          <p class="explanation">
            <strong>Explanation:</strong> {{ candidate.insight?.match_explanation }}
          </p>
        </div>
      </div>
    </div>

    <div v-if="!matchStore.loading && matchStore.filteredAndSortedMatches.length === 0" class="no-results">
      No candidates meet the minimum score criteria.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMatchStore } from '../stores/matchStore'
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const matchStore = useMatchStore()
const route = useRoute()

// Auto fetch when page loads with jobId
onMounted(() => {
  const jobId = route.params.jobId as string
  if (jobId) {
    matchStore.fetchMatches(Number(jobId))
  }
})
</script>

<style scoped>
/* Same beautiful styles as before + minor improvements */
.matching-page { padding: 20px; }

.job-header { 
  background: #f0f9ff; 
  padding: 20px; 
  border-radius: 12px; 
  margin-bottom: 24px; 
}

.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 20px;
}

.candidates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
  gap: 24px;
}

.candidate-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  position: relative;
}

.rank-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: #1e40af;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.1rem;
}

.match-score {
  font-size: 1.35rem;
  margin: 12px 0;
}

.score-value {
  color: #10b981;
  font-weight: 700;
}

.insights {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.detail-section {
  margin: 14px 0;
}

.no-results, .loading-state, .error-state {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}
</style>