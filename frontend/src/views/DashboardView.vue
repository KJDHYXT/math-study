<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { cardsApi, quizApi, reviewApi } from '../api/client'
import type { ReviewStats } from '../api/types'

const dueCount = ref(0)
const wrongCount = ref(0)
const cardTotal = ref(0)
const rstats = ref<ReviewStats | null>(null)

onMounted(async () => {
  try { dueCount.value = (await cardsApi.queue()).total } catch { dueCount.value = 0 }
  try { wrongCount.value = (await quizApi.wrong()).total } catch { wrongCount.value = 0 }
  try { cardTotal.value = (await cardsApi.list()).total } catch { cardTotal.value = 0 }
  try { rstats.value = await reviewApi.stats() } catch { rstats.value = null }
})

const shortcuts = [
  { to: '/review', label: '快速复习', desc: '高频短时多轮 · 糊/生回收', primary: true },
  { to: '/notes/new', label: '记一篇笔记', desc: '用 Markdown + LaTeX 整理知识点' },
  { to: '/quiz/prepare', label: '开始组卷刷题', desc: '按学科/知识点随机抽题' },
  { to: '/cards/review', label: '今日复习卡片', desc: '按遗忘曲线安排复习' },
  { to: '/knowledge/graph', label: '查看知识点图谱', desc: '梳理学习脉络与依赖' },
]
</script>

<template>
  <div>
    <h1 class="page-title">仪表盘</h1>
    <div class="grid grid-2">
      <div class="card">
        <h3>今日快速复习</h3>
        <p style="font-size: 34px; margin: 6px 0">{{ rstats?.today_count ?? 0 }}</p>
        <p class="muted" style="margin: 0 0 8px">已复习 · 连续 {{ rstats?.streak ?? 0 }} 天</p>
        <router-link to="/review" class="btn primary">去快速复习</router-link>
      </div>
      <div class="card">
        <h3>今日待复习卡片</h3>
        <p style="font-size: 34px; margin: 6px 0">{{ dueCount }}</p>
        <router-link to="/cards/review" class="btn primary">去复习</router-link>
      </div>
    </div>

    <div class="card mt" v-if="rstats && (rstats.weak_chapters.length || rstats.today_count > 0)">
      <h3>薄弱章节（糊/生）</h3>
      <div class="row mt" style="gap: 8px">
        <span v-for="w in rstats.weak_chapters" :key="w.chapter" class="badge danger">{{ w.chapter }} · {{ w.count }} 项</span>
        <span v-if="!rstats.weak_chapters.length" class="muted">暂无薄弱点，继续加油！</span>
      </div>
      <p class="muted" style="margin: 8px 0 0">掌握度：熟 {{ rstats.distribution.familiar }} · 糊 {{ rstats.distribution.hazy }} · 生 {{ rstats.distribution.unfamiliar }}</p>
    </div>

    <div class="card mt">
      <h3>快速开始</h3>
      <div class="grid grid-2 mt">
        <div v-for="s in shortcuts" :key="s.to" class="list-item">
          <router-link :to="s.to" style="font-weight: 600; text-decoration: none; color: var(--text)">{{ s.label }}</router-link>
          <p class="muted" style="margin: 4px 0 0">{{ s.desc }}</p>
        </div>
      </div>
      <p class="muted" style="margin-top: 12px">共 {{ cardTotal }} 张记忆卡片；错题本 {{ wrongCount }} 题。</p>
    </div>
  </div>
</template>
