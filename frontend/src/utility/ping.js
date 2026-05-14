import api from '@/axiosInstance'
import { auth } from '@/stores/auth'

export async function pingServer() {
  try {
    const res = await api.get('/accounts/get_user_profile_info')
    const user = res.data
    auth.isAuthenticated = true
    auth.user = user
    return user
  } catch (err) {
    // Only handle 401 silently
    if (err.response?.status === 401) {
      auth.isAuthenticated = false
      auth.user = null
      console.warn('[pingServer] Not authenticated, skipping')
    } else {
      console.error('[pingServer] Unexpected error:', err)
    }
  }
}
