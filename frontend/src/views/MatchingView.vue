<template>
  <div class="matching-page">
    <h1>🎯 Candidate Matching Results</h1>

    <div v-if="matchStore.currentJob" class="job-header">
      <h2>{{ matchStore.currentJob.job_title }}</h2>
      <p class="total">
        Total Candidates: <strong>{{ matchStore.matches.length }}</strong>
      </p>
    </div>

    <!-- Controls -->
    <div class="controls-bar">
      <div class="sort-controls">
        <label><strong>Sort By:</strong></label>

        <button
          :class="{ active: matchStore.sortBy === 'score' }"
          @click="setSort('score')"
        >
          Match Score
        </button>

        <button
          :class="{ active: matchStore.sortBy === 'experience' }"
          @click="setSort('experience')"
        >
          Experience
        </button>
      </div>

      <div class="filter-controls">
        <label>
          Min Score: {{ Math.round(matchStore.filterMinScore * 100) }}%
        </label>

        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          v-model="matchStore.filterMinScore"
        />
      </div>
    </div>

    <div v-if="matchStore.loading" class="loading-state">
      🔍 Finding best candidates...
    </div>

    <div v-else-if="matchStore.error" class="error-state">
      {{ matchStore.error }}
    </div>

    <div v-else class="candidates-grid">
      <div
        v-for="(candidate, index) in displayedCandidates"
        :key="candidate.id + '-' + candidate.final_score"
        class="candidate-card"
      >
        <div class="rank-badge">#{{ index + 1 }}</div>

        <h3>{{ candidate.name }}</h3>
        <p v-if="candidate.email" class="email">{{ candidate.email }}</p>

        <div class="match-score">
          Match Score:
          <span class="score-value">
            {{ (candidate.final_score * 100).toFixed(1) }}%
          </span>
        </div>

        <p>
          <strong>Experience:</strong>
          {{ candidate.experience_years || 0 }} years
        </p>

        <div class="download-section">
          <button
            @click="downloadResume(candidate.id)"
            class="download-btn"
          >
            📄 Download Resume
          </button>
        </div>

        <div class="insights">
          <h4>🤖 AI Recruiter Insight</h4>
          <p class="summary">{{ candidate.insight?.summary }}</p>
          <p class="explanation">
            <strong>Why this score?</strong>
            {{ candidate.insight?.match_explanation }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { useMatchStore } from "../stores/matchStore";

const matchStore = useMatchStore();
const route = useRoute();

onMounted(() => {
  const jobId = route.params.jobId as string;
  if (jobId) matchStore.fetchMatches(Number(jobId));
});

const setSort = (type: "score" | "experience") => {
  matchStore.setSortBy(type);
};

const downloadResume = async (candidateId: number) => {
  try {
    const response = await fetch(`http://localhost:8000/api/candidates/${candidateId}/download`);
    if (!response.ok) {
      throw new Error('Failed to download resume');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_${candidateId}.pdf`; // Default filename
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Download failed:', error);
    alert('Failed to download resume. Please try again.');
  }
};

const displayedCandidates = computed(() => {
  return matchStore.filteredAndSortedMatches;
});

const getMatchedSkills = (candidate: any) => {
  const jobSkills = (matchStore.currentJob?.required_skills || []).map((s: string) =>
    s.toLowerCase().trim()
  );

  return (candidate.skills || []).filter((s: string) =>
    jobSkills.includes(s.toLowerCase().trim())
  );
};

const getMissingSkills = (candidate: any) => {
  const jobSkills = (matchStore.currentJob?.required_skills || []).map((s: string) =>
    s.toLowerCase().trim()
  );

  return jobSkills.filter(
    (js: string) =>
      !(candidate.skills || []).some(
        (s: string) => s.toLowerCase().trim() === js
      )
  );
};
</script>

<style scoped>
.matching-page {
  padding: 30px;
  background: #f8fafc;
  min-height: 100vh;
  font-family: Inter, system-ui;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 20px;
}

.job-header {
  background: white;
  padding: 20px;
  border-radius: 14px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.controls-bar {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  background: white;
  padding: 16px;
  border-radius: 14px;
  margin-bottom: 25px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.sort-controls button {
  margin-left: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  transition: 0.2s;
}

.sort-controls button.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.candidates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.candidate-card {
  background: white;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease;
}

.candidate-card:hover {
  transform: translateY(-4px);
}

.rank-badge {
  display: inline-block;
  background: #eef2ff;
  color: #3730a3;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  margin-bottom: 10px;
}

.match-score {
  font-size: 15px;
  margin: 10px 0;
}

.score-value {
  font-weight: 700;
  color: #16a34a;
}

.download-section {
  margin: 12px 0;
}

.download-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.download-btn:hover {
  background: #2563eb;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.matched-tag {
  background: #dcfce7;
  color: #166534;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.missing-tag {
  background: #fee2e2;
  color: #991b1b;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.insights {
  margin-top: 14px;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 10px;
}
</style>