import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
    { path: '/upload-resume', name: 'upload-resume', component: () => import('../views/ResumeUploadView.vue') },
    { path: '/job-input', name: 'job-input', component: () => import('../views/JobInputView.vue') },
    { 
      path: '/matching/:jobId?', 
      name: 'matching', 
      component: () => import('../views/MatchingView.vue') 
    }
  ]
})

export default router