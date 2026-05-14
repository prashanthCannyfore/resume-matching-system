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
    filterMinScore: 0.0   // Show all candidates by default; user can raise via slider
  }),

 getters: {
  filteredAndSortedMatches(state) {
    console.log("👉 Getter triggered")

    // ✅ Always clone first
    let list = [...state.matches]

    // ✅ filter
    list = list.filter((m: any) => {
      const score = Number(m.final_score ?? 0)
      return score >= state.filterMinScore
    })

    console.log("After filter:", list.map(x => x.name))

    // ✅ sort
    if (state.sortBy === 'score') {
      list.sort((a: any, b: any) => {
        return (b.final_score ?? 0) - (a.final_score ?? 0)
      })
    } else {
      list.sort((a: any, b: any) => {
        return (b.experience_years ?? 0) - (a.experience_years ?? 0)
      })
    }

    // ✅ return new reference
    return [...list]
  }
},

  actions: {
   async fetchMatches(jobId: number) {
  this.loading = true
  this.error = null

  try {
    const res = await axios.post(`${API_BASE}/jobs/${jobId}/match`)

    this.currentJob = res.data

    // ✅ IMPORTANT FIX (force reactivity)
    this.matches = [...(res.data.matches || [])]

    console.log("✅ Matches set:", this.matches)

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