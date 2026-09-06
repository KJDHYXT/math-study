<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '../api/client'
import type { SearchResults } from '../api/types'

const router = useRouter()
const q = ref('')
const results = ref<SearchResults | null>(null)
const loading = ref(false)

async function doSearch() {
  if (!q.value.trim()) return
  loading.value = true
  try {
    results.value = await searchApi.search(q.value.trim())
  } finally {
    loading.value = false
  }
}

function goto(kind: string, id: number) {
  if (kind === 'notes') router.push(`/notes/${id}`)
  else if (kind === 'questions') router.push('/quiz')
  else if (kind === 'cards') router.push('/cards')
  else router.push('/knowledge')
}
</script>

<template>
  <div>
    <h1 class="page-title">全局检索</h1>
    <div class="card mb row">
      <input v-model="q" class="col-1" placeholder="搜索笔记/题目/卡片/知识点" @keyup.enter="doSearch" />
      <button class="btn primary" @click="doSearch">{{ loading ? '搜索中' : '搜索' }}</button>
    </div>

    <template v-if="results">
      <div v-for="(group, key) in { notes: results.notes, questions: results.questions, cards: results.cards, knowledge: results.knowledge }" :key="key" class="mb">
        <h3 class="mb" style="margin: 0 0 6px">{{ { notes: '笔记', questions: '题目', cards: '卡片', knowledge: '知识点' }[key] }}（{{ group.length }}）</h3>
        <div v-if="group.length === 0" class="muted">无</div>
        <div v-else>
          <div v-for="hit in group" :key="hit.id" class="list-item" style="cursor: pointer" @click="goto(key, hit.id)">
            <strong>{{ hit.title }}</strong>
            <p class="muted" style="margin: 4px 0 0">{{ hit.snippet }}</p>
          </div>
        </div>
      </div>
      <div v-if="!results.notes.length && !results.questions.length && !results.cards.length && !results.knowledge.length" class="empty">没有找到相关内容。</div>
    </template>
  </div>
</template>
