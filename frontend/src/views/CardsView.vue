<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { cardsApi, subjectsApi } from '../api/client'
import type { Card, Subject } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const cards = ref<Card[]>([])
const subjects = ref<Subject[]>([])
const subjectId = ref<number | undefined>()
const showForm = ref(false)
const front = ref('')
const back = ref('')
const createdAt = ref<number | undefined>()

async function load() {
  const res = await cardsApi.list({ subject_id: subjectId.value })
  cards.value = res.items
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length) createdAt.value = subjects.value[0].id
  await load()
})

async function create() {
  await cardsApi.create({ subject_id: createdAt.value!, front: front.value, back: back.value })
  showForm.value = false
  front.value = ''
  back.value = ''
  await load()
}

async function remove(c: Card) {
  if (!confirm('确认删除该卡片？')) return
  await cardsApi.remove(c.id)
  await load()
}

const statusLabel: Record<string, string> = { new: '新卡', learning: '学习中', reviewing: '复习中' }
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">记忆卡片</h1>
      <div class="row">
        <router-link to="/cards/review" class="btn primary">今日复习</router-link>
        <button class="btn" @click="showForm = !showForm">＋ 新建卡片</button>
      </div>
    </div>

    <div class="card mb row">
      <select v-model="subjectId" @change="load"><option :value="undefined">全部学科</option><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
    </div>

    <div v-if="showForm" class="card mb">
      <div class="row mb">
        <select v-model="createdAt" style="margin-bottom: 8px"><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
      </div>
      <input v-model="front" class="col-1 mb" placeholder="正面（问题）" style="width: 100%" />
      <input v-model="back" class="col-1 mb" placeholder="背面（答案）" style="width: 100%" />
      <button class="btn primary" @click="create">保存</button>
    </div>

    <div v-if="cards.length === 0" class="empty">还没有卡片。</div>
    <div v-for="c in cards" :key="c.id" class="list-item">
      <div class="row" style="justify-content: space-between">
        <div class="row" style="gap: 8px"><span class="badge">{{ statusLabel[c.status] }}</span><span class="badge">间隔 {{ c.interval }} 天</span></div>
        <button class="btn small danger" @click="remove(c)">删除</button>
      </div>
      <div style="margin-top: 8px"><MarkdownRenderer :content="c.front" /></div>
      <div style="margin-top: 6px; opacity: 0.8"><MarkdownRenderer :content="c.back" /></div>
      <p class="muted" style="margin: 8px 0 0">到复习日：{{ c.due_date }}</p>
    </div>
  </div>
</template>
