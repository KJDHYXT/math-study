import { defineStore } from 'pinia'
import type { QuizItem } from '../api/types'

// 刷题会话状态：保存当前组卷的题目与作答进度。对应文档 05 §3。
export const useQuizStore = defineStore('quiz', {
  state: () => ({
    sessionId: 0,
    questions: [] as QuizItem[],
    index: 0,
    score: 0,
  }),
  getters: {
    current(state): QuizItem | undefined {
      return state.questions[state.index]
    },
    finished(state): boolean {
      return state.index >= state.questions.length
    },
  },
  actions: {
    start(sessionId: number, questions: QuizItem[]) {
      this.sessionId = sessionId
      this.questions = questions
      this.index = 0
      this.score = 0
    },
    next(correct: boolean) {
      if (correct) this.score++
      this.index++
    },
  },
})
