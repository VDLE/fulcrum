<template>
  <v-container class="d-flex justify-center align-center login-container" fluid>
    <v-slide-y-transition mode="in-out">
      <v-card v-if="showCard" elevation="4" class="pa-8 login-card">
        <div class="text-center mb-6">
          <h1 class="login-title">Welcome Back</h1>
          <p class="login-subtitle">Log in to access your dashboard</p>
        </div>

        <v-form @submit.prevent="login">
          <v-text-field
            v-model="email"
            label="Email"
            type="email"
            required
            class="mb-4"
            density="comfortable"
            hide-details="auto"
          ></v-text-field>

          <v-text-field
            v-model="password"
            label="Password"
            type="password"
            required
            class="mb-6"
            density="comfortable"
            hide-details="auto"
          ></v-text-field>

          <v-btn
            :loading="loading"
            color="primary"
            type="submit"
            block
            size="large"
          >
            Log In
          </v-btn>

          <v-row justify="center" class="mt-6">
            <v-col cols="12" class="text-center">
              <p>
                Don’t have an account?
                <RouterLink to="/register" class="register-link"
                  >Register here</RouterLink
                >
              </p>
            </v-col>
          </v-row>

          <v-alert
            v-if="error"
            type="error"
            class="mt-4 center-text"
            variant="outlined"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card>
    </v-slide-y-transition>
  </v-container>
</template>

<script>
import api from '@/axiosInstance'
import Cookies from 'js-cookie'
import { pingServer } from '@/utility/ping'
export default {
  name: 'UserLogin',
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: '',
      showCard: false,
    }
  },
  methods: {
    async login() {
      this.loading = true
      this.error = ''

      try {
        const response = await api.post(
          `/accounts/login`,
          {
            email: this.email,
            password: this.password,
          },
          {
            headers: {
              Accept: 'application/json',
              'Content-Type': 'application/json',
            },
          },
        )

        console.log('Login response:', response.data)

        // If login works just redirect
        if (response.data.meta?.code === 200) {
          const profileUpdate = localStorage.getItem('pendingProfileUpdate')
          if (profileUpdate) {
            try {
              const parsed = JSON.parse(profileUpdate)
              await api.post('/accounts/update_user_profile', parsed, {
                headers: {
                  'Content-Type': 'application/json',
                  Accept: 'application/json',
                },
              })
              console.log('Profile updated after login')
              localStorage.removeItem('pendingProfileUpdate')
            } catch (e) {
              console.warn('Profile update failed after login:', e)
              // Optionally keep the item for retry later
            }
          }
          setTimeout(() => {
            this.$router.push({ name: 'UserStudies' })
          }, 500)
        } else {
          this.error = 'Login failed. Unexpected response.'
        }
      } catch (err) {
        console.error(err)
        this.error =
          err.response?.data?.error ||
          err.response?.data?.message ||
          'Login failed. Please check your credentials.'
      } finally {
        this.loading = false
      }
    },
  },
  async mounted() {
    this.showCard = true // trigger animation
    try {
      const response = await pingServer()
      if (response.status === 200) {
        // This prevents users from loading in login on their own
        // Now even if they did, there are protections to handle tokens
        // But this is a way to control the UI
        this.$router.push({ name: 'UserStudies' })
      }
    } catch (e) {
      // Don't redirect, just let user log in manually
    }
  },
}
</script>

<style scoped>
.center-text {
  text-align: center;
}
.login-container {
  height: 100vh;
  background: linear-gradient(to right, #f5f7fa, #c3cfe2);
}

.login-card {
  max-width: 480px;
  width: 100%;
  border-radius: 16px;
}

.login-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 4px;
  color: #333;
}

.login-subtitle {
  font-size: 1.1rem;
  color: #666;
}

.register-link {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.center-text {
  text-align: center;
}
</style>
