<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { notesApi } from '../api/client'
import type { Note } from '../api/types'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()
const note = ref<Note | null>(null)

onMounted(async () => {
  note.value = await notesApi.get(Number(route.params.id))
})
</script>

<template>
  <div>
    <div class="row mb">
      <button class="btn" @click="router.push('/notes')">← 返回</button>
      <button v-if="note" class="btn" @click="router.push(`/notes/${note.id}/edit`)">编辑</button>
    </div>
    <div v-if="note" class="card">
      <h1>{{ note.title }}</h1>
      <div class="row mb" style="gap: 6px">
        <span v-for="t in note.tags" :key="t" class="badge">{{ t }}</span>
      </div>
      <MarkdownRenderer :content="note.content" />
    </div>
    <div v-else class="empty">加载中…</div>
  </div>
</template>
