<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { questionsApi, subjectsApi, knowledgeApi } from '../api/client'
import type { Question, Subject, KnowledgePoint, QType } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const router = useRouter()
const questions = ref<Question[]>([])
const subjects = ref<Subject[]>([])
const knowledges = ref<KnowledgePoint[]>([])
const subjectId = ref<number | undefined>()
const qtype = ref<string | undefined>()
const difficulty = ref<number | undefined>()
const chapter = ref<number | undefined>()

const showForm = ref(false)
const f = ref({
  subject_id: undefined as number | undefined,
  qtype: 'calculation' as QType,
  number: '',
  content: '',
  answer: '',
  explanation: '',
  difficulty: 3,
  knowledge_ids: [] as number[],
  core_idea: '',
  stepsText: '',
  trapsText: '',
  image_path: '' as string | null,
})

const selectedFile = ref<File | null>(null)
const imagePreview = ref('')
const extracting = ref(false)
const extractError = ref('')

const types = [
  { v: 'calculation', label: '计算' },
  { v: 'proof', label: '证明' },
]

async function load() {
  const res = await questionsApi.list({ subject_id: subjectId.value, qtype: qtype.value, difficulty: difficulty.value, chapter: chapter.value })
  questions.value = res.items
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  knowledges.value = await knowledgeApi.list()
  if (subjects.value.length) f.value.subject_id = subjects.value[0].id
  await load()
})

function setFile(file: File) {
  selectedFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}
function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0] || null
  if (file) setFile(file)
  else { selectedFile.value = null; imagePreview.value = '' }
}
function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items || []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) { setFile(file); e.preventDefault() }
      break
    }
  }
}
function onDrop(e: DragEvent) {
  e.preventDefault()
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) setFile(file)
}
function onDragOver(e: DragEvent) { e.preventDefault() }

async function uploadImage() {
  if (!selectedFile.value) return
  const res = await questionsApi.uploadImage(selectedFile.value)
  f.value.image_path = res.path
  return res.url
}

async function extractFromImage() {
  if (!selectedFile.value) return
  extracting.value = true
  extractError.value = ''
  try {
    const draft = await questionsApi.extract(selectedFile.value)
    if (draft.content) f.value.content = draft.content
    if (draft.solve_type) f.value.qtype = draft.solve_type as QType
    if (draft.number) f.value.number = draft.number
    if (draft.core_idea) f.value.core_idea = draft.core_idea
    if (draft.steps?.length) f.value.stepsText = draft.steps.join('\n')
    if (draft.answer) f.value.answer = draft.answer
    if (draft.explanation) f.value.explanation = draft.explanation
  } catch (e: any) {
    extractError.value = e?.response?.data?.detail || 'AI 提取失败，可手动填写'
  } finally {
    extracting.value = false
  }
}

async function createQuestion() {
  if (!f.value.subject_id || !f.value.content || !f.value.answer) return
  if (selectedFile.value && !f.value.image_path) await uploadImage()
  const steps = f.value.stepsText.split('\n').map((s) => s.trim()).filter(Boolean) || null
  await questionsApi.create({
    subject_id: f.value.subject_id,
    qtype: f.value.qtype,
    content: f.value.content,
    answer: f.value.answer,
    explanation: f.value.explanation || undefined,
    difficulty: f.value.difficulty,
    number: f.value.number || undefined,
    knowledge_ids: f.value.knowledge_ids,
    core_idea: f.value.core_idea || undefined,
    steps: steps.length ? steps : undefined,
    traps: f.value.trapsText.split(',').map((x) => x.trim()).filter(Boolean) || undefined,
    image_path: f.value.image_path || undefined,
    source: f.value.image_path ? 'image' : 'manual',
  })
  f.value = { ...f.value, number: '', content: '', answer: '', explanation: '', core_idea: '', stepsText: '', trapsText: '', image_path: null, knowledge_ids: [] }
  selectedFile.value = null
  imagePreview.value = ''
  showForm.value = false
  await load()
}

async function remove(q: Question) {
  if (!confirm('确认删除该题？')) return
  await questionsApi.remove(q.id)
  await load()
}

function toggleKp(id: number) {
  if (f.value.knowledge_ids.includes(id)) f.value.knowledge_ids = f.value.knowledge_ids.filter((x) => x !== id)
  else f.value.knowledge_ids.push(id)
}

const typeLabel = (t: string) => types.find((x) => x.v === t)?.label ?? t
const chapterLabel = (q: Question): string => {
  if (q.chapter == null) return q.number ?? '未分章'
  const sec = q.section != null ? ` 第${q.section}节` : ''
  return `第${q.chapter}章${sec}${q.number ? ` · ${q.number}` : ''}`
}

function cleanStep(s: string): string {
  return s.replace(/^\s*\d+[.、)）:：]\s*/, '').trim()
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">题库</h1>
      <div class="row">
        <button class="btn" @click="showForm = !showForm">＋ 录入题目</button>
        <router-link to="/quiz/prepare" class="btn primary">组卷刷题</router-link>
        <router-link to="/quiz/wrong" class="btn">错题本</router-link>
      </div>
    </div>

    <div class="card mb row">
      <select v-model="subjectId" @change="load"><option :value="undefined">全部学科</option><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
      <select v-model="qtype" @change="load"><option :value="undefined">全部题型</option><option v-for="t in types" :key="t.v" :value="t.v">{{ t.label }}</option></select>
      <input v-model.number="chapter" type="number" placeholder="章（如 6）" style="width: 90px" @change="load" />
      <select v-model="difficulty" @change="load"><option :value="undefined">全部难度</option><option :value="1">1</option><option :value="2">2</option><option :value="3">3</option><option :value="4">4</option><option :value="5">5</option></select>
    </div>

    <div v-if="showForm" class="card mb">
      <h3>录入题目</h3>
      <div class="row mb" style="align-items: flex-start; gap: 16px">
        <div class="upload-zone" tabindex="0" @paste="onPaste" @dragover="onDragOver" @drop="onDrop" @click="$refs.fileInput.click()">
          <p class="muted" style="margin: 0 0 6px">题目图片（点击选择 / 拖拽 / Ctrl+V 粘贴截图）</p>
          <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="onFileChange" />
          <div class="row mt" style="gap: 8px">
            <button class="btn primary" :disabled="!selectedFile || extracting" @click.stop="extractFromImage">
              {{ extracting ? '提取中…' : '从图片提取核心思路/步骤' }}
            </button>
            <span v-if="!selectedFile" class="muted">尚无图片</span>
            <span v-else class="badge ok">已选择图片，可提取</span>
          </div>
          <p v-if="extractError" style="color: var(--danger); margin: 8px 0 0">{{ extractError }}</p>
        </div>
        <img v-if="imagePreview" :src="imagePreview" style="max-width: 180px; max-height: 140px; border: 1px solid var(--border); border-radius: 8px" />
      </div>

      <div class="row mb">
        <select v-model="f.subject_id"><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
        <select v-model="f.qtype"><option v-for="t in types" :key="t.v" :value="t.v">{{ t.label }}</option></select>
        <input v-model="f.number" class="col-1" placeholder="编号（如 6.2.2，自动分章）" />
        <select v-model.number="f.difficulty"><option :value="1">1</option><option :value="2">2</option><option :value="3">3</option><option :value="4">4</option><option :value="5">5</option></select>
      </div>
      <textarea v-model="f.content" class="col-1 mb" rows="3" placeholder="题干（支持 $...$ 公式）" style="width: 100%"></textarea>
      <input v-model="f.answer" class="col-1 mb" placeholder="参考答案（支持公式）" style="width: 100%" />
      <textarea v-model="f.explanation" class="col-1 mb" rows="2" placeholder="解析（可选）" style="width: 100%"></textarea>
      <textarea v-model="f.core_idea" class="col-1 mb" rows="2" placeholder="核心思路：这道题考什么、用什么方法" style="width: 100%"></textarea>
      <textarea v-model="f.stepsText" class="col-1 mb" rows="3" placeholder="简明操作步骤，每步一行" style="width: 100%"></textarea>
      <input v-model="f.trapsText" class="col-1 mb" placeholder="坑点/易错点（逗号分隔，如：换元忘回代, 漏常数C）" style="width: 100%" />

      <div class="row mb" style="gap: 6px"><span class="muted">知识点：</span><button v-for="kp in knowledges" :key="kp.id" class="btn small" :class="{ primary: f.knowledge_ids.includes(kp.id) }" @click="toggleKp(kp.id)">{{ kp.name }}</button></div>
      <button class="btn primary" @click="createQuestion">保存</button>
    </div>

    <div v-if="questions.length === 0" class="empty">题库为空，可录入题目或组卷刷题。</div>
    <div v-for="q in questions" :key="q.id" class="list-item">
      <div class="row" style="justify-content: space-between">
        <div class="row" style="gap: 8px">
          <span class="badge">{{ typeLabel(q.qtype) }}</span>
          <span class="badge" style="background:#eef4fb;color:#2f6f96">{{ chapterLabel(q) }}</span>
          <span class="badge">难度 {{ q.difficulty }}</span>
          <span v-if="q.source === 'image'" class="badge ok">图片提取</span>
        </div>
        <button class="btn small danger" @click="remove(q)">删除</button>
      </div>
      <div style="margin-top: 8px"><MarkdownRenderer :content="q.content" /></div>
      <MarkdownRenderer :content="`**答案：**${q.answer || ''}`" />
      <div v-if="q.core_idea" class="mt"><MarkdownRenderer :content="`**核心思路：**${q.core_idea}`" /></div>
      <ol v-if="q.steps && q.steps.length" class="mt">
        <li v-for="(s, i) in q.steps" :key="i"><MarkdownRenderer :content="cleanStep(s)" /></li>
      </ol>
      <div v-if="q.traps && q.traps.length" class="mt" style="display:flex;gap:6px;flex-wrap:wrap"><strong class="muted">⚠ 坑点：</strong><span v-for="(t,i) in q.traps" :key="i" class="badge danger">{{ t }}</span></div>
      <img v-if="q.image_path" :src="q.image_path.startsWith('/uploads') ? q.image_path : '/uploads/' + q.image_path.split('/').pop()" style="max-width: 260px; margin-top: 8px; border: 1px solid var(--border); border-radius: 8px" />
    </div>
  </div>
</template>

<style scoped>
.upload-zone {
  flex: 1;
  min-width: 260px;
  padding: 14px 16px;
  border: 1.5px dashed var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.upload-zone:focus,
.upload-zone:hover {
  border-color: var(--primary);
  background: #f7fbff;
}
</style>
