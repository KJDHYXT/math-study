// 契约类型，对应文档 04。与后端 Pydantic 结构保持一致。

export interface Subject {
  id: number
  name: string
  description: string | null
}

export interface KnowledgePoint {
  id: number
  subject_id: number
  name: string
  description: string | null
}

export interface GraphNode { id: number; name: string }
export interface GraphEdge { source: number; target: number }
export interface Graph { nodes: GraphNode[]; edges: GraphEdge[] }

export interface Note {
  id: number
  subject_id: number
  title: string
  content: string
  tags: string[]
  knowledge_ids: number[]
  created_at: string
  updated_at: string
}

export interface NoteList { items: Note[]; total: number }

export type QType = 'calculation' | 'proof'

export interface Question {
  id: number
  subject_id: number
  qtype: QType
  content: string
  options: string[] | null
  answer: string
  explanation: string | null
  difficulty: number
  knowledge_ids: number[]
  number: string | null
  chapter: number | null
  section: number | null
  core_idea: string | null
  steps: string[] | null
  traps: string[] | null
  image_path: string | null
  source: string | null
  created_at: string
}

export interface ExtractResult {
  content: string | null
  core_idea: string
  steps: string[]
  answer: string | null
  explanation: string | null
  category?: string | null
  number?: string | null
}

export interface UploadImageResult {
  path: string
  url: string
  size: number
}

export type EntryCategory = 'theorem' | 'proposition' | 'example'

export interface MathEntry {
  id: number
  subject_id: number
  category: EntryCategory
  solve_type: QType
  number: string | null
  chapter: number | null
  section: number | null
  content: string
  core_idea: string | null
  steps: string[] | null
  answer: string | null
  explanation: string | null
  traps: string[] | null
  image_path: string | null
  source: string
  created_at: string
}

export interface EntryList { items: MathEntry[]; total: number }

export interface QuestionList { items: Question[]; total: number }

export interface Card {
  id: number
  subject_id: number
  front: string
  back: string
  ease_factor: number
  interval: number
  repetitions: number
  due_date: string
  status: string
  knowledge_ids: number[]
  created_at: string
}

export interface CardList { items: Card[]; total: number }

export interface QuizItem { question: Question; order_index: number }
export interface QuizSession { session_id: number; questions: QuizItem[] }
export interface QuizAnswerResult { is_correct: boolean; correct_answer: string; explanation: string | null }
export interface QuizFinish { total: number; correct: number; wrong_ids: number[] }
export interface WrongItem { question: Question; wrong_count: number }
export interface WrongBook { items: WrongItem[]; total: number }

export interface SearchHit { id: number; title: string; snippet: string }
export interface SearchResults { notes: SearchHit[]; questions: SearchHit[]; cards: SearchHit[]; knowledge: SearchHit[] }

export interface Tag { id: number; name: string }

export interface ReviewItem {
  item_type: 'entry' | 'question'
  id: number
  subject_id: number
  category: string | null
  solve_type: string | null
  number: string | null
  chapter: number | null
  section: number | null
  front: string
  core_idea: string | null
  steps: string[] | null
  answer: string | null
  explanation: string | null
  traps: string[] | null
}

export interface ReviewBatch { items: ReviewItem[]; total: number }

export interface ReviewStats {
  today_count: number
  streak: number
  distribution: { unfamiliar: number; hazy: number; familiar: number }
  weak_chapters: { chapter: string; count: number }[]
}
