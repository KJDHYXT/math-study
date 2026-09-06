import { defineStore } from 'pinia'
import { subjectsApi } from '../api/client'
import type { Subject } from '../api/types'

export const useSubjectStore = defineStore('subjects', {
  state: () => ({ subjects: [] as Subject[], loaded: false }),
  actions: {
    async load(force = false) {
      if (this.loaded && !force) return
      this.subjects = await subjectsApi.list()
      this.loaded = true
    },
  },
})
