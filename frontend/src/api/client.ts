// API 客户端与业务接口封装。对应文档 04。
import axios from 'axios'
import type {
  Card, CardList, Graph, KnowledgePoint, Note, NoteList, Question, QuestionList,
  QuizAnswerResult, QuizFinish, QuizSession, SearchResults, Subject, Tag, WrongBook,
  ExtractResult, UploadImageResult, MathEntry, EntryList, EntryCategory,
  ReviewBatch, ReviewStats,
} from './types'

const baseURL = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'

export const api = axios.create({ baseURL })

// 请求拦截器：附加 Bearer token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截器：统一错误处理与 401 跳转
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export type Rating = 'again' | 'hard' | 'good' | 'easy'

// 学科
export const subjectsApi = {
  list: () => api.get<Subject[]>('/subjects').then((r) => r.data),
  create: (payload: { name: string; description?: string }) => api.post<Subject>('/subjects', payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/subjects/${id}`),
}

// 标签
export const tagsApi = {
  list: () => api.get<Tag[]>('/tags').then((r) => r.data),
  create: (name: string) => api.post<Tag>('/tags', { name }).then((r) => r.data),
}

// 知识点
export const knowledgeApi = {
  list: (subject_id?: number) => api.get<KnowledgePoint[]>('/knowledge', { params: { subject_id } }).then((r) => r.data),
  create: (payload: { subject_id: number; name: string; description?: string }) => api.post<KnowledgePoint>('/knowledge', payload).then((r) => r.data),
  graph: (subject_id?: number) => api.get<Graph>('/knowledge/graph', { params: { subject_id } }).then((r) => r.data),
  addRelation: (source_id: number, target_id: number) => api.post('/knowledge/relations', { source_id, target_id }),
  removeRelation: (source_id: number, target_id: number) => api.delete('/knowledge/relations', { params: { source_id, target_id } }),
  related: (id: number) => api.get(`/knowledge/${id}/related`).then((r) => r.data),
}

// 笔记
export const notesApi = {
  list: (params?: { subject_id?: number; tag?: string; knowledge_id?: number; q?: string }) => api.get<NoteList>('/notes', { params }).then((r) => r.data),
  get: (id: number) => api.get<Note>(`/notes/${id}`).then((r) => r.data),
  create: (payload: { subject_id: number; title: string; content: string; tags?: string[]; knowledge_ids?: number[] }) => api.post<Note>('/notes', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Pick<Note, 'title' | 'content' | 'tags' | 'knowledge_ids'>>) => api.put<Note>(`/notes/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/notes/${id}`),
}

// 题目
export const questionsApi = {
  list: (params?: { subject_id?: number; knowledge_id?: number; qtype?: string; difficulty?: number; chapter?: number; q?: string }) => api.get<QuestionList>('/questions', { params }).then((r) => r.data),
  get: (id: number) => api.get<Question>(`/questions/${id}`).then((r) => r.data),
  create: (payload: Partial<Question> & { subject_id: number; content: string; answer: string }) => api.post<Question>('/questions', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Question>) => api.put<Question>(`/questions/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/questions/${id}`),
  uploadImage: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<UploadImageResult>('/questions/upload-image', fd).then((r) => r.data)
  },
  extract: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<ExtractResult>('/questions/extract', fd).then((r) => r.data)
  },
}

// 数学条目（定理/命题/例题）
export const entriesApi = {
  list: (params?: { category?: EntryCategory; subject_id?: number; chapter?: number; q?: string }) => api.get<EntryList>('/entries', { params }).then((r) => r.data),
  create: (payload: Partial<MathEntry> & { subject_id: number; category: EntryCategory; content: string }) => api.post<MathEntry>('/entries', payload).then((r) => r.data),
  get: (id: number) => api.get<MathEntry>(`/entries/${id}`).then((r) => r.data),
  update: (id: number, payload: Partial<MathEntry>) => api.put<MathEntry>(`/entries/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/entries/${id}`),
  uploadImage: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<UploadImageResult>('/questions/upload-image', fd).then((r) => r.data)
  },
  extract: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post<ExtractResult>('/entries/extract', fd).then((r) => r.data)
  },
}
export const quizApi = {
  createSession: (payload: { subject_id?: number; knowledge_ids?: number[]; count?: number; qtype?: string; difficulty?: number }) => api.post<QuizSession>('/quiz/sessions', payload).then((r) => r.data),
  submit: (session_id: number, payload: { question_id: number; user_answer: string | null; self_correct?: boolean }) =>
    api.post<QuizAnswerResult>(`/quiz/sessions/${session_id}/answers`, payload).then((r) => r.data),
  finish: (session_id: number) => api.post<QuizFinish>(`/quiz/sessions/${session_id}/finish`).then((r) => r.data),
  wrong: (subject_id?: number) => api.get<WrongBook>('/quiz/wrong', { params: { subject_id } }).then((r) => r.data),
}

// 卡片
export const cardsApi = {
  list: (params?: { subject_id?: number; knowledge_id?: number; status?: string; due?: boolean }) => api.get<CardList>('/cards', { params }).then((r) => r.data),
  create: (payload: { subject_id: number; front: string; back: string; knowledge_ids?: number[] }) => api.post<Card>('/cards', payload).then((r) => r.data),
  update: (id: number, payload: Partial<Pick<Card, 'front' | 'back' | 'knowledge_ids'>>) => api.put<Card>(`/cards/${id}`, payload).then((r) => r.data),
  remove: (id: number) => api.delete(`/cards/${id}`),
  queue: (subject_id?: number) => api.get<CardList>('/cards/review/queue', { params: { subject_id } }).then((r) => r.data),
  review: (id: number, rating: Rating) => api.post(`/cards/${id}/review`, { rating }).then((r) => r.data),
  history: (id: number) => api.get(`/cards/${id}/history`).then((r) => r.data),
}

// 检索
export const searchApi = {
  search: (q: string) => api.get<SearchResults>('/search', { params: { q } }).then((r) => r.data),
}

// 认证
export const authApi = {
  login: (token: string) => api.post<{ token: string; valid: boolean }>('/auth/login', { token }).then((r) => r.data),
  verify: () => api.get('/auth/verify').then((r) => r.data),
}

// 快速复习
export const reviewApi = {
  items: (params?: { type?: string; subject_id?: number; chapter?: number; category?: string; qtype?: string; count?: number }) => api.get<ReviewBatch>('/review/items', { params }).then((r) => r.data),
  submit: (payload: { item_type: string; item_id: number; mastery: string }) => api.post('/review/submit', payload).then((r) => r.data),
  stats: () => api.get<ReviewStats>('/review/stats').then((r) => r.data),
}
