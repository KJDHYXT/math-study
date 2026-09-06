<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { knowledgeApi, subjectsApi } from '../api/client'
import type { KnowledgePoint, Subject } from '../api/types'

const router = useRouter()
const subjects = ref<Subject[]>([])
const knowledges = ref<KnowledgePoint[]>([])
const subjectId = ref<number | undefined>()
const showForm = ref(false)
const name = ref('')
const description = ref('')
const srcId = ref<number | undefined>()
const tgtId = ref<number | undefined>()

async function load() {
  knowledges.value = await knowledgeApi.list(subjectId.value)
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length) subjectId.value = subjects.value[0].id
  await load()
})

async function create() {
  if (!subjectId.value || !name.value) return
  await knowledgeApi.create({ subject_id: subjectId.value, name: name.value, description: description.value })
  name.value = ''
  description.value = ''
  await load()
}

async function addRelation() {
  if (!srcId.value || !tgtId.value) return
  await knowledgeApi.addRelation(srcId.value, tgtId.value)
  alert('已添加依赖')
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">知识点</h1>
      <div class="row">
        <router-link to="/knowledge/graph" class="btn primary">图谱</router-link>
        <button class="btn" @click="showForm = !showForm">＋ 新建知识点</button>
      </div>
    </div>

    <div class="card mb row">
      <select v-model="subjectId" @change="load"><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
    </div>

    <div v-if="showForm" class="card mb">
      <input v-model="name" class="col-1 mb" placeholder="知识点名称，如：柯西收敛准则" style="width: 100%" />
      <input v-model="description" class="col-1 mb" placeholder="简介（可含 LaTeX 公式）" style="width: 100%" />
      <button class="btn primary" @click="create">保存</button>
    </div>

    <div class="card mb row">
      <span class="muted">建立依赖（源 → 目标，源为前提）：</span>
      <select v-model="srcId"><option :value="undefined">源知识点</option><option v-for="k in knowledges" :key="k.id" :value="k.id">{{ k.name }}</option></select>
      <span>→</span>
      <select v-model="tgtId"><option :value="undefined">目标知识点</option><option v-for="k in knowledges" :key="k.id" :value="k.id">{{ k.name }}</option></select>
      <button class="btn primary" @click="addRelation">添加</button>
    </div>

    <div v-if="knowledges.length === 0" class="empty">还没有知识点。</div>
    <div v-for="k in knowledges" :key="k.id" class="list-item">
      <strong>{{ k.name }}</strong>
      <p v-if="k.description" class="muted" style="margin: 6px 0 0">{{ k.description }}</p>
    </div>
  </div>
</template>
