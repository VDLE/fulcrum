<template>
  <v-app-bar color="primary">
    <v-app-bar-title>Fulcrum</v-app-bar-title>

    <v-spacer></v-spacer>

    <!-- Always show About button -->
    <v-btn icon @click="goToAbout">
      <v-icon>mdi-help-circle-outline</v-icon>
    </v-btn>

    <!-- Only show if user is authenticated -->
    <template v-if="auth.isAuthenticated">
      <v-menu
        v-model="menuOpen"
        offset-y
        transition="slide-y-transition"
        @update:modelValue="onMenuToggle"
      >
        <template #activator="{ props }">
          <v-btn icon v-bind="props" size="large">
            <v-avatar color="primary" size="48">
              <v-icon size="32">mdi-account-circle</v-icon>
            </v-avatar>
          </v-btn>
        </template>

        <v-slide-y-transition mode="in-out">
          <v-card style="min-width: 320px; padding: 8px">
            <v-list-item class="px-4 py-3">
              <v-row align="center" no-gutters style="width: 100%">
                <v-col cols="auto">
                  <v-avatar size="40">
                    <img
                      src="/images/unr n.jpg"
                      alt="User"
                      style="
                        width: 100%;
                        height: 100%;
                        object-fit: cover;
                        border-radius: 50%;
                      "
                    />
                  </v-avatar>
                </v-col>
                <v-col class="pl-3">
                  <span class="text-subtitle-1 font-weight-medium">
                    {{ displayName }}
                  </span>
                </v-col>
              </v-row>
            </v-list-item>

            <v-divider class="my-2" />

            <v-list>
              <v-list-item @click="goToProfile" class="px-4">
                <v-row align="center" no-gutters style="width: 100%">
                  <v-col cols="auto">
                    <v-icon>mdi-account</v-icon>
                  </v-col>
                  <v-col class="pl-3">
                    <span class="text-subtitle-2">Edit Profile</span>
                  </v-col>
                  <v-col cols="auto">
                    <v-icon>mdi-chevron-right</v-icon>
                  </v-col>
                </v-row>
              </v-list-item>

              <v-list-item @click="logOut" class="px-4">
                <v-row align="center" no-gutters style="width: 100%">
                  <v-col cols="auto">
                    <v-icon>mdi-logout</v-icon>
                  </v-col>
                  <v-col class="pl-3">
                    <span class="text-subtitle-2">Logout</span>
                  </v-col>
                  <v-col cols="auto">
                    <v-icon>mdi-chevron-right</v-icon>
                  </v-col>
                </v-row>
              </v-list-item>
            </v-list>
          </v-card>
        </v-slide-y-transition>
      </v-menu>
    </template>
  </v-app-bar>
</template>

<script>
import api from '@/axiosInstance'
import { auth } from '@/stores/auth'
import { useStudyStore } from '@/stores/study'

export default {
  name: 'GlobalTopBar',
  data() {
    return {
      displayName: 'Loading...',
      auth,
      menuOpen: false,
    }
  },
  watch: {
    'auth.user': {
      handler(newUser) {
        if (newUser) {
          const fullName =
            `${newUser.first_name || ''} ${newUser.last_name || ''}`.trim()
          this.displayName = fullName || newUser.email || 'Unknown User'
        }
      },
      immediate: true,
    },
  },
  methods: {
    goToProfile() {
      this.$router.push({ name: 'UserProfile' })
    },
    goToAbout() {
      this.$router.push({ name: 'AboutPage' })
    },
    async logOut() {
      try {
        const response = await api.post('/accounts/logout')
        if (response.status === 200) {
          auth.isAuthenticated = false
          auth.user = null
          const studyStore = useStudyStore()
          studyStore.reset()
          this.$router.push({ name: 'UserLogin' })
        }
      } catch (err) {
        console.error('Error logging out:', err)
      }
    },
    onMenuToggle(isOpen) {
      if (isOpen) {
        this.fetchUserInfo()
      }
    },
    async fetchUserInfo() {
      try {
        const res = await api.get('/accounts/get_user_profile_info')
        if (res.data) {
          auth.user = res.data
        }
      } catch (err) {
        console.error('Failed to refresh user info:', err)
      }
    },
  },
}
</script>
