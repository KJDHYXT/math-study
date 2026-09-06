<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { knowledgeApi, subjectsApi } from '../api/client'
import type { Graph, Subject } from '../api/types'

const W = 900
const H = 640
const subjects = ref<Subject[]>([])
const subjectId = ref<number | undefined>()
const graph = ref<Graph>({ nodes: [], edges: [] })
const positions = ref<{ x: number; y: number }[]>([])
const selected = ref<number | null>(null)
const related = ref<{ notes: any[]; questions: any[]; cards: any[] } | null>(null)

const nodeById = computed(() => {
  const m = new Map<number, { id: number; name: string }>()
  graph.value.nodes.forEach((n) => m.set(n.id, n))
  return m
})

const nodeIndex = computed(() => {
  const m = new Map<number, number>()
  graph.value.nodes.forEach((n, i) => m.set(n.id, i))
  return m
})

function idx(id: number): number | undefined {
  return nodeIndex.value.get(id)
}

async function load() {
  graph.value = await knowledgeApi.graph(subjectId.value)
  computeLayout()
}

onMounted(async () => {
  subjects.value = await subjectsApi.list()
  if (subjects.value.length) subjectId.value = subjects.value[0].id
  await load()
})

// 简化的力导向布局（斥力 + 弹簧 + 向心），迭代后得到稳定位置。
function computeLayout() {
  const n = graph.value.nodes.length
  if (n === 0) { positions.value = []; return }
  const pos = Array.from({ length: n }, (_, i) => {
    const ang = (2 * Math.PI * i) / Math.max(n, 1)
    const r = Math.min(W, H) / 2.6
    return { x: W / 2 + r * Math.cos(ang), y: H / 2 + r * Math.sin(ang) }
  })
  const idxMap = new Map<number, number>()
  graph.value.nodes.forEach((nd, i) => idxMap.set(nd.id, i))

  const repulsion = 2400
  const springLen = 130
  const springK = 0.03
  const gravity = 0.02
  const iterations = 350

  for (let it = 0; it < iterations; it++) {
    const disp = Array.from({ length: n }, () => ({ x: 0, y: 0 }))
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i === j) continue
        const dx = pos[i].x - pos[j].x
        const dy = pos[i].y - pos[j].y
        const d = Math.sqrt(dx * dx + dy * dy) || 0.01
        const force = repulsion / (d * d)
        disp[i].x += (dx / d) * force
        disp[i].y += (dy / d) * force
      }
      disp[i].x += (W / 2 - pos[i].x) * gravity
      disp[i].y += (H / 2 - pos[i].y) * gravity
    }
    graph.value.edges.forEach((e) => {
      const a = idxMap.get(e.source)! as number
      const b = idxMap.get(e.target)! as number
      const dx = pos[b].x - pos[a].x
      const dy = pos[b].y - pos[a].y
      const d = Math.sqrt(dx * dx + dy * dy) || 0.01
      const force = springK * (d - springLen)
      const fx = (dx / d) * force
      const fy = (dy / d) * force
      disp[a].x += fx; disp[a].y += fy
      disp[b].x -= fx; disp[b].y -= fy
    })
    for (let i = 0; i < n; i++) {
      pos[i].x += Math.max(-8, Math.min(8, disp[i].x))
      pos[i].y += Math.max(-8, Math.min(8, disp[i].y))
      pos[i].x = Math.max(60, Math.min(W - 60, pos[i].x))
      pos[i].y = Math.max(40, Math.min(H - 40, pos[i].y))
    }
  }
  positions.value = pos
}

async function select(id: number) {
  selected.value = id
  related.value = await knowledgeApi.related(id)
}

function degreeOf(id: number): number {
  return graph.value.edges.reduce((acc, e) => acc + (e.source === id || e.target === id ? 1 : 0), 0)
}
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">知识点图谱</h1>
      <div class="row">
        <select v-model="subjectId" @change="load">
          <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
        <router-link to="/knowledge" class="btn">返回列表</router-link>
      </div>
    </div>

    <div class="card" style="padding: 0; overflow: hidden">
      <svg v-if="graph.nodes.length" :width="W" :height="H" style="width: 100%; max-width: 100%">
        <line
          v-for="(e, i) in graph.edges" :key="'e' + i"
          :x1="positions[idx(e.source)]?.x" :y1="positions[idx(e.source)]?.y"
          :x2="positions[idx(e.target)]?.x" :y2="positions[idx(e.target)]?.y"
          stroke="#c3ccd6" stroke-width="1.5"
        />
        <g v-for="(nd, i) in graph.nodes" :key="nd.id">
          <circle
            :cx="positions[i]?.x" :cy="positions[i]?.y" :r="14 + degreeOf(nd.id) * 2"
            :fill="selected === nd.id ? '#3b8dbd' : '#6ea8c9'" stroke="#2f6f96" stroke-width="1.5"
            style="cursor: pointer" @click="select(nd.id)"
          />
          <text :x="positions[i]?.x" :y="positions[i]?.y - 22" text-anchor="middle" font-size="12" fill="#23272f">{{ nd.name }}</text>
        </g>
      </svg>
      <div v-else class="empty">暂无知识点，去列表新建。</div>
    </div>

    <div v-if="related" class="card mt">
      <h3>关联内容（{{ nodeById.get(selected!)?.name }}）</h3>
      <div class="grid grid-2">
        <div>
          <p class="muted">笔记</p>
          <p v-if="related.notes.length === 0" class="muted">无</p>
          <div v-for="n in related.notes" :key="n.id" class="list-item"><router-link :to="`/notes/${n.id}`">{{ n.title }}</router-link></div>
        </div>
        <div>
          <p class="muted">题目</p>
          <p v-if="related.questions.length === 0" class="muted">无</p>
          <div v-for="x in related.questions" :key="x.id" class="list-item">{{ x.content.slice(0, 50) }}</div>
        </div>
        <div>
          <p class="muted">卡片</p>
          <p v-if="related.cards.length === 0" class="muted">无</p>
          <div v-for="c in related.cards" :key="c.id" class="list-item">{{ c.front.slice(0, 50) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
