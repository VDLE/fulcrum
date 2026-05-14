<template>
  <v-container
    class="d-flex justify-center align-center register-container"
    fluid
  >
    <v-slide-y-transition mode="in-out">
      <v-card v-if="showCard" elevation="4" class="pa-8 register-card">
        <div class="text-center mb-6">
          <h1 class="register-title">Create an Account</h1>
          <p class="register-subtitle">Sign up to get started</p>
        </div>

        <v-form @submit.prevent="register">
          <v-text-field
            v-model="firstName"
            label="First Name"
            required
            class="mb-4"
            density="comfortable"
            hide-details="auto"
          />

          <v-text-field
            v-model="lastName"
            label="Last Name"
            required
            class="mb-4"
            density="comfortable"
            hide-details="auto"
          />

          <v-text-field
            v-model="email"
            label="Email"
            type="email"
            required
            class="mb-4"
            density="comfortable"
            hide-details="auto"
          />

          <v-text-field
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            label="Password"
            :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="showPassword = !showPassword"
            required
            class="mb-4"
            density="comfortable"
            hide-details="auto"
          />

          <v-text-field
            v-model="passwordConfirm"
            :type="showPassword ? 'text' : 'password'"
            label="Confirm Password"
            :error="showPasswordMismatch"
            :error-messages="
              showPasswordMismatch ? ['Passwords do not match'] : []
            "
            required
            class="mb-6"
            density="comfortable"
            hide-details="auto"
          />

          <v-btn
            :loading="loading"
            type="submit"
            color="primary"
            block
            size="large"
            :disabled="!passwordsMatch"
          >
            Register
          </v-btn>

          <v-alert
            v-if="error"
            type="error"
            class="mt-4 text-center"
            variant="outlined"
          >
            {{ error }}
          </v-alert>

          <v-alert
            v-if="success"
            type="success"
            class="mt-4 text-center"
            variant="outlined"
          >
            {{ success }}
          </v-alert>

          <v-row justify="center" class="mt-6">
            <v-col cols="12" class="text-center">
              <p>
                Already have an account?
                <RouterLink to="/UserLogin" class="login-link"
                  >Log in</RouterLink
                >
              </p>
            </v-col>
          </v-row>
        </v-form>
      </v-card>
    </v-slide-y-transition>
  </v-container>
</template>

<script>
import api from '@/axiosInstance'

export default {
  name: 'UserRegister',
  data() {
    return {
      email: '',
      password: '',
      passwordConfirm: '',
      firstName: '',
      lastName: '',
      loading: false,
      error: '',
      success: '',
      showPassword: false,
      showCard: false,
    }
  },
  mounted() {
    this.showCard = true
  },
  computed: {
    passwordsMatch() {
      return this.password === this.passwordConfirm && this.password !== ''
    },
    showPasswordMismatch() {
      return (
        this.passwordConfirm !== '' &&
        this.password !== '' &&
        this.password !== this.passwordConfirm
      )
    },
  },
  methods: {
    async register() {
      this.loading = true
      this.error = ''
      this.success = ''

      try {
        const response = await api.post(
          '/accounts/register',
          {
            email: this.email,
            password: this.password,
          },
          {
            headers: {
              'Content-Type': 'application/json',
              Accept: 'application/json',
            },
          },
        )

        if (response.status === 200 || response.status === 201) {
          // Save name temporarily
          localStorage.setItem(
            'pendingProfileUpdate',
            JSON.stringify({
              first_name: this.firstName,
              last_name: this.lastName,
              username: this.email, // Or whatever identifier you want to send
            }),
          )
          this.success =
            'Registration successful! Please check your email to confirm.'
        } else {
          this.error = 'Registration failed. Please try again.'
        }
      } catch (err) {
        const data = err.response?.data
        const fieldErrors = data?.response?.field_errors
        const errors = data?.response?.errors
        if (fieldErrors && Object.keys(fieldErrors).length) {
          this.error = Object.values(fieldErrors).flat().join(' ')
        } else if (errors && errors.length) {
          this.error = errors.join(' ')
        } else {
          this.error = data?.error || 'Registration failed. Please try again.'
        }
      } finally {
        this.loading = false
      }
    },
  },
}
</script>
