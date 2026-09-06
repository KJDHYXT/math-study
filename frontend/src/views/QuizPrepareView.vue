<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi, subjectsApi, knowledgeApi } from '../api/client'
import type { Subject, KnowledgePoint } from '../api/types'
import { useQuizStore } from '../stores/quiz'

const router = useRouter()
const quizStore = useQuizStore()
const subjects = ref<Subject[]>([])
const knowledges = ref<KnowledgePoint[]>([])
const subjectId = ref<number | undefined>()
const knowledgeIds = ref<number[]>([])
const count = ref(10)
const qtype = ref<string | undefined>()
const loading = ref(false)

const types = [
  { v: '', label: '全部题型' },
  { v: 'calculation', label: '计算' },
  { v: 'proof', label: '证明' },
]

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  knowledges.value = await knowledgeApi.list()
})

async function start() {
  loading.value = true
  try {
    const sess = await quizApi.createSession({
      subject_id: subjectId.value,
      knowledge_ids: knowledgeIds.value,
      count: count.value,
      qtype: qtype.value || undefined,
    })
    quizStore.start(sess.session_id, sess.questions)
    router.push(`/quiz/session/${sess.session_id}`)
  } finally {
    loading.value = false
  }
}

function toggleKp(id: number) {
  if (knowledgeIds.value.includes(id)) knowledgeIds.value = knowledgeIds.value.filter((x) => x !== id)
  else knowledgeIds.value.push(id)
}
</script>

<template>
  <div>
    <h1 class="page-title">组卷刷题</h1>
    <div class="card" style="max-width: 520px">
      <div class="mb">
        <p class="muted" style="margin: 0 0 6px">学科</p>
        <select v-model="subjectId"><option :value="undefined">不限学科</option><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
      </div>
      <div class="mb">
        <p class="muted" style="margin: 0 0 6px">题型</p>
        <select v-model="qtype"><option v-for="t in types" :key="t.v" :value="t.v">{{ t.label }}</option></select>
      </div>
      <div class="mb">
        <p class="muted" style="margin: 0 0 6px">题量（不足则取全部）</p>
        <input v-model.number="count" type="number" min="1" style="width: 90px" />
      </div>
      <div class="mb">
        <p class="muted" style="margin: 0 0 6px">限定知识点</p>
        <div class="row" style="gap: 6px">
          <button v-for="kp in knowledges" :key="kp.id" class="btn small" :class="{ primary: knowledgeIds.includes(kp.id) }" @click="toggleKp(kp.id)">{{ kp.name }}</button>
        </div>
      </div>
      <button class="btn primary mt" :disabled="loading" @click="start">{{ loading ? '组卷中…' : '开始刷题' }}</button>
    </div>
  </div>
</template>
