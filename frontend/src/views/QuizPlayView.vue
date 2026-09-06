<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '../api/client'
import { useQuizStore } from '../stores/quiz'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const router = useRouter()
const quizStore = useQuizStore()

const selected = ref('')
const selfCorrect = ref(true)
const feedback = ref<{ is_correct: boolean; correct_answer: string; explanation: string | null } | null>(null)
const submitting = ref(false)

const current = computed(() => quizStore.current)
const progress = computed(() => (quizStore.questions.length ? `${quizStore.index + 1}/${quizStore.questions.length}` : '0/0'))

function submit() {
  if (!current.value || feedback.value) return
  submitting.value = true
  const question = current.value.question
  quizApi
    .submit(quizStore.sessionId, {
      question_id: question.id,
      user_answer: selected.value || null,
      self_correct: selfCorrect.value,
    })
    .then((r) => { feedback.value = r })
    .finally(() => { submitting.value = false })
}

function next() {
  if (!feedback.value) return
  quizStore.next(feedback.value.is_correct)
  selected.value = ''
  selfCorrect.value = true
  feedback.value = null
  if (quizStore.finished) {
    quizApi.finish(quizStore.sessionId)
    router.push('/quiz/wrong')
  }
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">刷题作答</h1>
      <span class="muted">{{ progress }}</span>
    </div>

    <div v-if="current" class="card">
      <div class="row mb"><span class="badge">{{ current.question.qtype === 'proof' ? '证明' : '计算' }}</span><span class="badge">难度 {{ current.question.difficulty }}</span></div>
      <MarkdownRenderer :content="current.question.content" />

      <div class="mt">
        <textarea v-model="selected" rows="4" class="col-1" placeholder="写下你的计算/证明过程（可选），然后自评是否答对" style="width: 100%"></textarea>
        <div class="row mt" style="gap: 8px">
          <button class="btn" :class="{ primary: selfCorrect }" @click="selfCorrect = true">我答对了</button>
          <button class="btn" :class="{ danger: !selfCorrect }" @click="selfCorrect = false">我答错了</button>
        </div>
      </div>

      <button class="btn primary mt" :disabled="submitting || feedback" @click="submit">{{ submitting ? '提交中' : '提交自评' }}</button>

      <div v-if="feedback" class="mt" style="padding: 12px; border: 1px solid var(--border); border-radius: 8px">
        <span :class="feedback.is_correct ? 'badge ok' : 'badge danger'">{{ feedback.is_correct ? '✔ 正确' : '✘ 待订正' }}</span>
        <p style="margin: 8px 0 0">参考答案：<MarkdownRenderer :content="feedback.correct_answer" /></p>
        <p v-if="feedback.explanation" class="muted">解析：{{ feedback.explanation }}</p>
        <button class="btn primary mt" @click="next">{{ quizStore.finished ? '完成' : '下一题' }}</button>
      </div>
    </div>

    <div v-else class="empty">本组题目为空，请重新组卷。<router-link to="/quiz/prepare">去组卷</router-link></div>
  </div>
</template>
