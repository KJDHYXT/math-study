<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { notesApi, subjectsApi } from '../api/client'
import type { Note, Subject } from '../api/types'

const router = useRouter()
const notes = ref<Note[]>([])
const subjects = ref<Subject[]>([])
const subjectId = ref<number | undefined>()
const keyword = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await notesApi.list({
      subject_id: subjectId.value,
      q: keyword.value || undefined,
    })
    notes.value = res.items
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  await load()
})

function edit(note: Note) {
  router.push(`/notes/${note.id}/edit`)
}
function open(note: Note) {
  router.push(`/notes/${note.id}`)
}
async function remove(note: Note) {
  if (!confirm('确认删除该笔记？')) return
  await notesApi.remove(note.id)
  await load()
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">笔记</h1>
      <router-link to="/notes/new" class="btn primary">＋ 新建笔记</router-link>
    </div>

    <div class="card mb row">
      <select v-model="subjectId" @change="load">
        <option :value="undefined">全部学科</option>
        <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
      <input v-model="keyword" class="col-1" placeholder="搜索标题/内容" @keyup.enter="load" />
      <button class="btn" @click="load">搜索</button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="notes.length === 0" class="empty">还没有笔记，点击右上角创建。</div>
    <div v-else>
      <div v-for="note in notes" :key="note.id" class="list-item">
        <div class="row" style="justify-content: space-between">
          <a @click="open(note)" style="font-weight: 600; cursor: pointer; color: var(--text)">{{ note.title }}</a>
          <div class="row">
            <button class="btn small" @click="edit(note)">编辑</button>
            <button class="btn small danger" @click="remove(note)">删除</button>
          </div>
        </div>
        <div class="row mt" style="gap: 6px">
          <span v-for="t in note.tags" :key="t" class="badge">{{ t }}</span>
        </div>
        <p class="muted" style="margin: 8px 0 0">{{ note.updated_at }}</p>
      </div>
    </div>
  </div>
</template>
