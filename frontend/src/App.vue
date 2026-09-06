<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loginPage = computed(() => route.name === 'login')

const nav = [
  { to: '/', label: '仪表盘', icon: '🏠' },
  { to: '/notes', label: '笔记', icon: '📝' },
  { to: '/quiz', label: '题库刷题', icon: '📚' },
  { to: '/cards', label: '记忆卡片', icon: '🗂️' },
  { to: '/review', label: '快速复习', icon: '⚡' },
  { to: '/knowledge', label: '知识点', icon: '🧩' },
  { to: '/entries', label: '数学条目', icon: '📌' },
  { to: '/search', label: '检索', icon: '🔍' },
]

function isActive(to: string): boolean {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div v-if="loginPage" class="login-wrap">
    <router-view />
  </div>
  <div v-else class="app-layout">
    <aside class="sidebar">
      <h1 class="brand">数学学硕备考</h1>
      <p class="subtitle">学习与复习专区</p>
      <nav class="nav">
        <router-link
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <span class="icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <button v-if="auth.isLoggedIn" class="nav-item logout" @click="logout">退出</button>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style>
/* 顶部留出占位，样式在 styles.css 深化 */
</style>
