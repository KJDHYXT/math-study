<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { cardsApi } from '../api/client'
import type { Card, Rating } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const queue = ref<Card[]>([])
const index = ref(0)
const revealed = ref(false)
const loading = ref(true)
const done = ref(0)

const current = computed(() => queue.value[index.value])
const progress = computed(() => (queue.value.length ? `${index.value}/${queue.value.length}` : '0/0'))

async function load() {
  loading.value = true
  const res = await cardsApi.queue()
  queue.value = res.items
  loading.value = false
}

onMounted(load)

async function rate(rating: Rating) {
  if (!current.value) return
  await cardsApi.review(current.value.id, rating)
  done.value++
  index.value++
  revealed.value = false
}
</script>

<template>
  <div>
    <h1 class="page-title">今日复习</h1>
    <div class="row mb" style="justify-content: space-between">
      <span class="muted">{{ progress }}</span>
      <span class="badge">已完成 {{ done }}</span>
    </div>

    <div v-if="loading" class="empty">加载复习队列…</div>
    <div v-else-if="queue.length === 0" class="empty">
      今天没有要复习的卡片 🎉
    </div>
    <div v-else-if="current" class="card" style="max-width: 720px; margin: 0 auto; min-height: 240px; display: flex; flex-direction: column; justify-content: center;">
      <div v-if="!revealed">
        <p class="muted" style="text-align: center">正面</p>
        <div style="text-align: center"><MarkdownRenderer :content="current.front" /></div>
        <div class="row" style="justify-content: center; margin-top: 24px">
          <button class="btn primary" @click="revealed = true">显示答案</button>
        </div>
      </div>
      <div v-else>
        <p class="muted" style="text-align: center">正面</p>
        <div style="text-align: center"><MarkdownRenderer :content="current.front" /></div>
        <hr style="margin: 12px 0" />
        <p class="muted" style="text-align: center">背面</p>
        <div style="text-align: center"><MarkdownRenderer :content="current.back" /></div>
        <div class="row" style="justify-content: center; margin-top: 24px; gap: 8px">
          <button class="btn danger" @click="rate('again')">忘记</button>
          <button class="btn" @click="rate('hard')">模糊</button>
          <button class="btn primary" @click="rate('good')">记得</button>
          <button class="btn" @click="rate('easy')">简单</button>
        </div>
      </div>
    </div>
    <div v-else class="empty">本组复习完成！</div>
  </div>
</template>
