<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { reviewApi, subjectsApi } from '../api/client'
import type { Subject, ReviewItem } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const MAX_ROUND = 3
const subjects = ref<Subject[]>([])
const stage = ref<'setup' | 'session' | 'done'>('setup')
const setup = ref({ type: 'mixed', subject_id: undefined as number | undefined, category: undefined as string | undefined, qtype: undefined as string | undefined, chapter: undefined as number | undefined, count: 12 })
const queue = ref<{ item: ReviewItem; round: number }[]>([])
const revealed = ref(false)
const loading = ref(false)
const error = ref('')
const reviewed = ref(0)
const dist = ref({ familiar: 0, hazy: 0, unfamiliar: 0 })

const typeOptions = [
  { v: 'mixed', label: '混合（数学条目+题目）' },
  { v: 'entry', label: '数学条目(定理/命题/例题)' },
  { v: 'question', label: '题目(计算/证明)' },
]
const catOptions = [
  { v: undefined, label: '全部类别' },
  { v: 'theorem', label: '定理' },
  { v: 'proposition', label: '命题' },
  { v: 'example', label: '例题' },
]
const qtypeOptions = [
  { v: undefined, label: '全部题型' },
  { v: 'calculation', label: '计算' },
  { v: 'proof', label: '证明' },
]

const current = computed(() => queue.value[0])
const modeLabel = computed(() => (current.value?.item.item_type === 'entry' ? '数学条目' : '题目'))
const masterLabels: Record<string, string> = { unfamiliar: '生', hazy: '糊', familiar: '熟' }

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length) setup.value.subject_id = subjects.value[0].id
})

async function start() {
  loading.value = true
  error.value = ''
  try {
    const res = await reviewApi.items({
      type: setup.value.type,
      subject_id: setup.value.subject_id,
      category: setup.value.category,
      qtype: setup.value.qtype,
      chapter: setup.value.chapter,
      count: setup.value.count,
    })
    if (res.total === 0) { error.value = '没有匹配的复习内容'; return }
    queue.value = res.items.map((it) => ({ item: it, round: 1 }))
    reviewed.value = 0
    dist.value = { familiar: 0, hazy: 0, unfamiliar: 0 }
    revealed.value = false
    stage.value = 'session'
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function reveal() {
  revealed.value = true
}

function cleanStep(s: string): string {
  return s.replace(/^\s*\d+[.、)）:：]\s*/, '').trim()
}
function imgSrc(p: string): string { return p.startsWith('/') ? p : '/uploads/' + p.split('/').pop() }

async function assess(mastery: string) {
  const cur = current.value
  if (!cur || !revealed.value) return
  await reviewApi.submit({ item_type: cur.item.item_type, item_id: cur.item.id, mastery })
  queue.value.shift()
  reviewed.value++
  dist.value[mastery as keyof typeof dist.value]++
  // 糊/生 且未超轮数 → 本轮再出现（插到约 2 项后）
  if (mastery !== 'familiar' && cur.round < MAX_ROUND && queue.value.length > 0) {
    const pos = Math.min(2, queue.value.length)
    queue.value.splice(pos, 0, { item: cur.item, round: cur.round + 1 })
  }
  revealed.value = false
  if (queue.value.length === 0) stage.value = 'done'
}

function redo() { stage.value = 'setup' }
</script>

<template>
  <div>
    <!-- 设置 -->
    <div v-if="stage === 'setup'" style="max-width: 560px">
      <h1 class="page-title">快速复习</h1>
      <div class="card">
        <p class="muted">高频短时多轮：展示 → 主动回忆 → 看答案 → 自评(熟/糊/生)。糊/生的项会本轮再现。</p>
        <div class="mb"><p class="muted" style="margin:0 0 6px">复习对象</p>
          <select v-model="setup.type"><option v-for="t in typeOptions" :key="t.v" :value="t.v">{{ t.label }}</option></select>
        </div>
        <div class="mb"><p class="muted" style="margin:0 0 6px">学科</p>
          <select v-model="setup.subject_id"><option :value="undefined">全部</option><option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option></select>
        </div>
        <div class="row mb" style="gap: 10px">
          <div style="flex:1"><p class="muted" style="margin:0 0 6px">类别</p>
            <select v-model="setup.category"><option v-for="c in catOptions" :key="String(c.v)" :value="c.v">{{ c.label }}</option></select>
          </div>
          <div style="flex:1"><p class="muted" style="margin:0 0 6px">题型</p>
            <select v-model="setup.qtype"><option v-for="t in qtypeOptions" :key="String(t.v)" :value="t.v">{{ t.label }}</option></select>
          </div>
        </div>
        <div class="row mb" style="gap: 10px">
          <div style="flex:1"><p class="muted" style="margin:0 0 6px">章(如 6，可空)</p>
            <input v-model.number="setup.chapter" type="number" style="width:100%" /></div>
          <div style="flex:1"><p class="muted" style="margin:0 0 6px">数量</p>
            <input v-model.number="setup.count" type="number" min="1" style="width:100%" /></div>
        </div>
        <p v-if="error" style="color:var(--danger)">{{ error }}</p>
        <button class="btn primary" :disabled="loading" @click="start">{{ loading ? '加载中…' : '开始复习' }}</button>
      </div>
    </div>

    <!-- 会话 -->
    <div v-else-if="stage === 'session'" class="card" style="max-width: 760px; margin: 0 auto; min-height: 340px; display:flex; flex-direction:column">
      <div class="row mb" style="justify-content:space-between">
        <span class="muted">{{ modeLabel }} · {{ current?.item?.number || '未编号' }}</span>
        <span class="badge">剩余 {{ queue.length }}</span>
      </div>
      <div class="row mb" style="gap:8px">
        <span v-if="current.item.category" class="badge">{{ {theorem:'定理',proposition:'命题',example:'例题'}[current.item.category] }}</span>
        <span class="badge">{{ current.item.solve_type === 'proof' ? '证明' : '计算' }}</span>
        <span v-if="current.item.chapter != null" class="badge">第{{ current.item.chapter }}章{{ current.item.section != null ? ' 第'+current.item.section+'节':'' }}</span>
        <span class="badge" :style="{background:'#fbecec',color:'#d64545'}">第{{ current.round }}轮</span>
      </div>

      <div v-if="!revealed" class="review-front"><MarkdownRenderer :content="current.item.front" /></div>

      <div v-if="revealed" class="review-box">
        <p class="muted" style="margin:0 0 6px">框框</p>
        <MarkdownRenderer :content="current.item.front" />
        <div v-if="current.item.core_idea" class="mt"><MarkdownRenderer :content="`**核心思路：**${current.item.core_idea}`" /></div>
        <div v-if="current.item.answer" class="mt"><MarkdownRenderer :content="`**结论/答案：**${current.item.answer}`" /></div>
        <ol v-if="current.item.steps && current.item.steps.length" class="mt"><li v-for="(s,i) in current.item.steps" :key="i"><MarkdownRenderer :content="cleanStep(s)" /></li></ol>
        <div v-if="current.item.explanation" class="mt"><MarkdownRenderer :content="`**解析：**${current.item.explanation}`" /></div>
        <div v-if="current.item.traps && current.item.traps.length" class="trap-warn mt">
          <strong>⚠ 坑点/易错：</strong>
          <span v-for="(t,i) in current.item.traps" :key="i" class="badge danger">{{ t }}</span>
        </div>
        <img v-if="current.item.image_path" :src="imgSrc(current.item.image_path)" style="max-width:260px;margin-top:8px;border:1px solid var(--border);border-radius:8px" />
      </div>

      <div class="mt" style="margin-top:auto">
        <button v-if="!revealed" class="btn primary" @click="reveal">显示框框/答案</button>
        <div v-else class="row" style="gap:8px">
          <button class="btn danger" @click="assess('unfamiliar')">生(陌生)</button>
          <button class="btn" @click="assess('hazy')">糊(模糊)</button>
          <button class="btn ok" @click="assess('familiar')">熟(记住)</button>
        </div>
      </div>
    </div>

    <!-- 结束 -->
    <div v-else class="card" style="max-width:560px;margin:0 auto;text-align:center">
      <h2>本轮完成 🎉</h2>
      <p>共复习 {{ reviewed }} 项 · 熟 {{ dist.familiar }} · 糊 {{ dist.hazy }} · 生 {{ dist.unfamiliar }}</p>
      <p class="muted">糊/生的项可在下一轮继续，或回到题库/数学条目中补充「坑点」。</p>
      <div class="row mt" style="justify-content:center"><button class="btn primary" @click="redo">再来一轮</button></div>
    </div>
  </div>
</template>

<style scoped>
.review-front { font-size: 18px; line-height: 1.6; flex: 1; }
.review-box { flex: 1; background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 12px; }
.trap-warn { background: #fff4f4; border: 1px solid #f5c2c2; border-radius: 8px; padding: 8px 10px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
</style>
