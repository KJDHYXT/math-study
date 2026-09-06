<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { entriesApi, subjectsApi } from '../api/client'
import type { MathEntry, Subject, EntryCategory, QType } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const entries = ref<MathEntry[]>([])
const subjects = ref<Subject[]>([])
const subjectId = ref<number | undefined>()
const categoryFilter = ref<EntryCategory | undefined>()
const chapter = ref<number | undefined>()
const showForm = ref(false)

const f = ref({
  subject_id: undefined as number | undefined,
  category: 'example' as EntryCategory,
  solve_type: 'calculation' as QType,
  number: '',
  content: '',
  answer: '',
  explanation: '',
  core_idea: '',
  stepsText: '',
  trapsText: '',
  image_path: '' as string | null,
})

const selectedFile = ref<File | null>(null)
const imagePreview = ref('')
const extracting = ref(false)
const extractError = ref('')

const catLabel: Record<string, string> = { theorem: '定理', proposition: '命题', example: '例题' }
const catClass: Record<string, string> = { theorem: 'cat-theorem', proposition: 'cat-prop', example: 'cat-ex' }
const cats: { v: EntryCategory; label: string }[] = [
  { v: 'theorem', label: '定理' },
  { v: 'proposition', label: '命题' },
  { v: 'example', label: '例题' },
]
const solveTypes = [
  { v: 'calculation', label: '计算' },
  { v: 'proof', label: '证明' },
]
const solveLabel = (t: string) => (t === 'proof' ? '证明' : '计算')

async function load() {
  const res = await entriesApi.list({ category: categoryFilter.value, subject_id: subjectId.value, chapter: chapter.value })
  entries.value = res.items
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
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
  const res = await entriesApi.uploadImage(selectedFile.value)
  f.value.image_path = res.path
  return res.url
}

async function extractFromImage() {
  if (!selectedFile.value) return
  extracting.value = true
  extractError.value = ''
  try {
    const draft = await entriesApi.extract(selectedFile.value)
    if (draft.content) f.value.content = draft.content
    if (draft.category) f.value.category = draft.category as EntryCategory
    if (draft.solve_type) f.value.solve_type = draft.solve_type as QType
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

async function createEntry() {
  if (!f.value.subject_id || !f.value.content) return
  if (selectedFile.value && !f.value.image_path) await uploadImage()
  const steps = f.value.stepsText.split('\n').map((s) => s.trim()).filter(Boolean) || null
  await entriesApi.create({
    subject_id: f.value.subject_id,
    category: f.value.category,
    solve_type: f.value.solve_type,
    number: f.value.number || undefined,
    content: f.value.content,
    core_idea: f.value.core_idea || undefined,
    steps: steps.length ? steps : undefined,
    traps: f.value.trapsText.split(',').map((x) => x.trim()).filter(Boolean) || undefined,
    answer: f.value.answer || undefined,
    explanation: f.value.explanation || undefined,
    image_path: f.value.image_path || undefined,
    source: f.value.image_path ? 'image' : 'manual',
  })
  Object.assign(f.value, { number: '', content: '', answer: '', explanation: '', core_idea: '', stepsText: '', trapsText: '', image_path: null })
  selectedFile.value = null
  imagePreview.value = ''
  showForm.value = false
  await load()
}

async function remove(e: MathEntry) {
  if (!confirm('确认删除该条目？')) return
  await entriesApi.remove(e.id)
  await load()
}

function cleanStep(s: string): string {
  return s.replace(/^\s*\d+[.、)）:：]\s*/, '').trim()
}
function imgSrc(p: string): string {
  return p.startsWith('/') ? p : '/uploads/' + p.split('/').pop()
}
function chapterLabel(e: MathEntry): string {
  if (e.chapter != null) {
    const sec = e.section != null ? ` 第${e.section}节` : ''
    return `第${e.chapter}章${sec}${e.number ? ` · ${e.number}` : ''}`
  }
  return e.number ?? '未分章'
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">数学条目（定理 / 命题 / 例题）</h1>
      <button class="btn" @click="showForm = !showForm">＋ 新建条目</button>
    </div>

    <div class="card mb row">
      <select v-model="categoryFilter" @change="load">
        <option :value="undefined">全部类别</option>
        <option v-for="c in cats" :key="c.v" :value="c.v">{{ c.label }}</option>
      </select>
      <select v-model="subjectId" @change="load"><option :value="undefined">全部学科</option><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
      <input v-model.number="chapter" type="number" placeholder="章（如 6）" style="width: 90px" @change="load" />
    </div>

    <div v-if="showForm" class="card mb">
      <h3>录入数学条目</h3>
      <div class="row mb" style="align-items: flex-start; gap: 16px">
        <div class="upload-zone" tabindex="0" @paste="onPaste" @dragover="onDragOver" @drop="onDrop" @click="$refs.fileInput.click()">
          <p class="muted" style="margin: 0 0 6px">内容图片（点击选择 / 拖拽 / Ctrl+V 粘贴截图）</p>
          <input ref="fileInput" type="file" accept="image/*" style="display: none" @change="onFileChange" />
          <div class="row mt" style="gap: 8px">
            <button class="btn primary" :disabled="!selectedFile || extracting" @click.stop="extractFromImage">
              {{ extracting ? '提取中…' : '从图片提取并自动分类' }}
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
        <select v-model="f.category">
          <option v-for="c in cats" :key="c.v" :value="c.v">{{ c.label }}</option>
        </select>
        <select v-model="f.solve_type">
          <option v-for="t in solveTypes" :key="t.v" :value="t.v">{{ t.label }}</option>
        </select>
        <input v-model="f.number" class="col-1" placeholder="编号（如 6.2.2、5.1，自动分章）" />
      </div>
      <textarea v-model="f.content" class="col-1 mb" rows="3" placeholder="定理/命题/例题内容（支持 $...$ 公式）" style="width: 100%"></textarea>
      <input v-model="f.answer" class="col-1 mb" placeholder="结论/答案（若有，支持公式）" style="width: 100%" />
      <textarea v-model="f.core_idea" class="col-1 mb" rows="2" placeholder="核心思路（可选）" style="width: 100%"></textarea>
      <textarea v-model="f.stepsText" class="col-1 mb" rows="3" placeholder="简明步骤，每行一步（可选）" style="width: 100%"></textarea>
      <input v-model="f.trapsText" class="col-1 mb" placeholder="坑点/易错点（逗号分隔，可选）" style="width: 100%" />
      <textarea v-model="f.explanation" class="col-1 mb" rows="2" placeholder="解析/说明（可选）" style="width: 100%"></textarea>
      <button class="btn primary" @click="createEntry">保存</button>
    </div>

    <div v-if="entries.length === 0" class="empty">还没有数学条目。</div>
    <div v-for="e in entries" :key="e.id" class="list-item">
      <div class="row" style="justify-content: space-between">
        <div class="row" style="gap: 8px">
          <span class="badge" :class="catClass[e.category]">{{ catLabel[e.category] }}<template v-if="e.number"> {{ e.number }}</template></span>
          <span class="badge">{{ solveLabel(e.solve_type) }}</span>
          <span class="badge" style="background:#eef4fb;color:#2f6f96">{{ chapterLabel(e) }}</span>
          <span v-if="e.source === 'image'" class="badge ok">图片</span>
        </div>
        <button class="btn small danger" @click="remove(e)">删除</button>
      </div>
      <div style="margin-top: 8px"><MarkdownRenderer :content="e.content" /></div>
      <div v-if="e.answer" class="mt"><MarkdownRenderer :content="`**结论/答案：**${e.answer}`" /></div>
      <div v-if="e.core_idea" class="mt"><MarkdownRenderer :content="`**核心思路：**${e.core_idea}`" /></div>
      <ol v-if="e.steps && e.steps.length" class="mt">
        <li v-for="(s, i) in e.steps" :key="i"><MarkdownRenderer :content="cleanStep(s)" /></li>
      </ol>
      <div v-if="e.explanation" class="mt"><MarkdownRenderer :content="`**解析：**${e.explanation}`" /></div>
      <div v-if="e.traps && e.traps.length" class="mt" style="display:flex;gap:6px;flex-wrap:wrap"><strong class="muted">⚠ 坑点：</strong><span v-for="(t,i) in e.traps" :key="i" class="badge danger">{{ t }}</span></div>
      <img v-if="e.image_path" :src="imgSrc(e.image_path)" style="max-width: 260px; margin-top: 8px; border: 1px solid var(--border); border-radius: 8px" />
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
.cat-theorem { background: #e7f0fb; color: #2f6f96; }
.cat-prop { background: #e8f5ee; color: var(--ok); }
.cat-ex { background: #fff3e6; color: #b06a2a; }
</style>
