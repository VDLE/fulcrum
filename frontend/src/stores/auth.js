import { reactive } from 'vue'

export const auth = reactive({
  isAuthenticated: false,
  user: null,
})
