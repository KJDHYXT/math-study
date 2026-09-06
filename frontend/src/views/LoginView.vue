<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const pass = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await auth.login(pass.value)
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败，请检查口令'
  }
}
</script>

<template>
  <div class="card" style="width: 360px; max-width: 90vw">
    <h2>登录</h2>
    <p class="muted">输入访问口令（跨设备访问时启用鉴权；本机已关闭鉴权可跳过）。</p>
    <form @submit.prevent="submit" class="row" style="margin-top: 12px">
      <input v-model="pass" type="password" placeholder="访问口令" class="col-1" />
      <button class="btn primary" type="submit">登录</button>
    </form>
    <p v-if="error" class="danger-text" style="color: var(--danger); margin-top: 10px">{{ error }}</p>
    <button class="btn mt" @click="router.push('/')">本机直接使用</button>
  </div>
</template>

<style>
.danger-text { color: var(--danger); }
</style>
