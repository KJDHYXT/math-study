import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 对应文档 05 §2 路由表。
const routes: RouteRecordRaw[] = [
  { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/notes', name: 'notes', component: () => import('../views/NotesView.vue') },
  { path: '/notes/new', name: 'note-new', component: () => import('../views/NoteEditorView.vue') },
  { path: '/notes/:id', name: 'note-detail', component: () => import('../views/NoteDetailView.vue') },
  { path: '/notes/:id/edit', name: 'note-edit', component: () => import('../views/NoteEditorView.vue') },
  { path: '/quiz', name: 'quiz', component: () => import('../views/QuizView.vue') },
  { path: '/quiz/prepare', name: 'quiz-prepare', component: () => import('../views/QuizPrepareView.vue') },
  { path: '/quiz/session/:id', name: 'quiz-session', component: () => import('../views/QuizPlayView.vue') },
  { path: '/quiz/wrong', name: 'quiz-wrong', component: () => import('../views/WrongBookView.vue') },
  { path: '/cards', name: 'cards', component: () => import('../views/CardsView.vue') },
  { path: '/cards/review', name: 'cards-review', component: () => import('../views/ReviewView.vue') },
  { path: '/review', name: 'quick-review', component: () => import('../views/QuickReview.vue') },
  { path: '/knowledge', name: 'knowledge', component: () => import('../views/KnowledgeView.vue') },
  { path: '/knowledge/graph', name: 'knowledge-graph', component: () => import('../views/KnowledgeGraphView.vue') },
  { path: '/entries', name: 'entries', component: () => import('../views/EntriesView.vue') },
  { path: '/search', name: 'search', component: () => import('../views/SearchView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
