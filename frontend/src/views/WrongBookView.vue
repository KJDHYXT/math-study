<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { quizApi } from '../api/client'
import type { WrongItem } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const router = useRouter()
const items = ref<WrongItem[]>([])

const typeLabel = (t: string) => (t === 'proof' ? '证明' : '计算')

onMounted(async () => {
  const res = await quizApi.wrong()
  items.value = res.items
})
</script>

<template>
  <div>
    <div class="row mb" style="justify-content: space-between">
      <h1 class="page-title" style="margin: 0">错题本</h1>
      <button class="btn" @click="router.push('/quiz')">返回题库</button>
    </div>
    <div v-if="items.length === 0" class="empty">暂无错题，继续加油！</div>
    <div v-for="item in items" :key="item.question.id" class="list-item">
      <div class="row" style="justify-content: space-between">
        <div class="row" style="gap: 8px"><span class="badge">{{ typeLabel(item.question.qtype) }}</span><span class="badge danger">错 {{ item.wrong_count }} 次</span></div>
      </div>
      <div style="margin-top: 8px"><MarkdownRenderer :content="item.question.content" /></div>
      <p class="muted" style="margin: 8px 0 0">正确答案：{{ item.question.answer }}</p>
      <p v-if="item.question.explanation" class="muted">解析：{{ item.question.explanation }}</p>
    </div>
  </div>
</template>
