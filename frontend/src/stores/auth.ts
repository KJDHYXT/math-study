import { defineStore } from 'pinia'
import { authApi } from '../api/client'

// 认证 store：token 持久化到 localStorage。对应文档 05 §3。
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') ?? '',
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
  },
  actions: {
    async login(pass: string) {
      const res = await authApi.login(pass)
      this.token = res.token
      localStorage.setItem('access_token', res.token)
    },
    logout() {
      this.token = ''
      localStorage.removeItem('access_token')
    },
  },
})
