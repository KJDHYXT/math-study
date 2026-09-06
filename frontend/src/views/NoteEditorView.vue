<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notesApi, subjectsApi, knowledgeApi } from '../api/client'
import type { Subject, KnowledgePoint } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()
const editingId = computed(() => (route.params.id ? Number(route.params.id) : null))

const subjects = ref<Subject[]>([])
const knowledges = ref<KnowledgePoint[]>([])
const subjectId = ref<number | undefined>(undefined)
const title = ref('')
const content = ref('')
const tags = ref('')
const knowledgeIds = ref<number[]>([])
const preview = ref(false)

const tabs = ['$$', '^', '_', '\\frac{a}{b}', '\\int', '\\lim']

async function load() {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length) subjectId.value = subjects.value[0].id
  knowledges.value = await knowledgeApi.list()
  if (editingId.value) {
    const note = await notesApi.get(editingId.value)
    subjectId.value = note.subject_id
    title.value = note.title
    content.value = note.content
    tags.value = note.tags.join(',')
    knowledgeIds.value = note.knowledge_ids
  }
}

onMounted(load)

async function save() {
  const payload = {
    subject_id: subjectId.value!,
    title: title.value,
    content: content.value,
    tags: tags.value.split(',').map((s) => s.trim()).filter(Boolean),
    knowledge_ids: knowledgeIds.value,
  }
  if (editingId.value) {
    await notesApi.update(editingId.value, payload)
  } else {
    await notesApi.create(payload)
  }
  router.push('/notes')
}

function insertMath(expr: string) {
  content.value = content.value + ` $${expr}$ `
}

function toggleKp(id: number) {
  if (knowledgeIds.value.includes(id)) {
    knowledgeIds.value = knowledgeIds.value.filter((x) => x !== id)
  } else {
    knowledgeIds.value.push(id)
  }
}
</script>

<template>
  <div>
    <h1 class="page-title">{{ editingId ? '编辑笔记' : '新建笔记' }}</h1>
    <div class="row mb">
      <button class="btn" @click="router.push('/notes')">← 返回</button>
      <button class="btn primary" @click="save">保存</button>
      <button class="btn" @click="preview = !preview">{{ preview ? '编辑' : '预览' }}</button>
    </div>

    <div class="card">
      <div class="row mb">
        <select v-model="subjectId">
          <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <input v-model="title" class="col-1" placeholder="笔记标题" />
      </div>

      <div class="row mb" style="gap: 6px">
        <span class="muted">插入公式：</span>
        <button v-for="t in tabs" :key="t" class="btn small" @click="insertMath(t)">{{ t }}</button>
      </div>

      <div class="row mb" style="gap: 8px; align-items: flex-start">
        <textarea
          v-model="content"
          class="col-1"
          rows="12"
          placeholder="使用 Markdown 编写，支持 $...$ 行内公式与 $$...$$ 块级公式"
        ></textarea>
        <div v-if="preview" class="col-1 card" style="padding: 14px">
          <MarkdownRenderer :content="content" />
        </div>
      </div>

      <div class="row mb">
        <input v-model="tags" class="col-1" placeholder="标签，用逗号分隔，如：极限, ε-δ" />
      </div>

      <div class="mb">
        <p class="muted" style="margin: 0 0 6px">关联知识点：</p>
        <div class="row" style="gap: 6px">
          <button
            v-for="kp in knowledges"
            :key="kp.id"
            class="btn small"
            :class="{ primary: knowledgeIds.includes(kp.id) }"
            @click="toggleKp(kp.id)"
          >{{ kp.name }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
