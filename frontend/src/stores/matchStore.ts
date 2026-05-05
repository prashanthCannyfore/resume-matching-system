import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

export const useMatchStore = defineStore('match', {
  state: () => ({
    currentJob: null as any,
    matches: [] as any[],
    loading: false,
    error: null as string | null,
    sortBy: 'score' as 'score' | 'experience',
    filterMinScore: 0.4   // Default 40%
  }),

  getters: {
    filteredAndSortedMatches(state) {
      let list = state.matches.filter((m: any) => m.score >= state.filterMinScore)

      if (state.sortBy === 'score') {
        return [...list].sort((a: any, b: any) => b.score - a.score)
      } else {
        return [...list].sort((a: any, b: any) => 
          (b.experience_years || 0) - (a.experience_years || 0)
        )
      }
    }
  },

  actions: {
    async fetchMatches(jobId: number) {
      this.loading = true
      this.error = null

      try {
        const res = await axios.post(`${API_BASE}/jobs/${jobId}/match`)
        this.currentJob = res.data
        this.matches = res.data.matches || []
      } catch (err: any) {
        this.error = err.response?.data?.detail || 'Failed to load matching candidates'
        console.error('Match API Error:', err)
      } finally {
        this.loading = false
      }
    },

    setSortBy(sort: 'score' | 'experience') {
      this.sortBy = sort
    },

    setMinScore(score: number) {
      this.filterMinScore = Math.max(0, Math.min(1, score))
    },

    reset() {
      this.currentJob = null
      this.matches = []
      this.error = null
    }
  }
})