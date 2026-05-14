<template>
  <v-main>
    <v-container class="mt-5 profile-page">
      <!-- Banner and Avatar -->
      <div class="banner-container">
        <v-img src="/images/convert.jpg" class="banner-img" cover></v-img>

        <div class="avatar-wrapper">
          <v-avatar class="profile-avatar" size="120">
            <v-img src="/images/unr n.jpg" alt="User Avatar" contain></v-img>
          </v-avatar>
        </div>
      </div>

      <!-- Profile Form -->
      <v-card class="pa-6 mt-6" elevation="2">
        <v-tabs v-model="tab" background-color="transparent" grow>
          <v-tab>Profile</v-tab>
          <v-tab>Change Password</v-tab>
        </v-tabs>

        <v-window v-model="tab" class="mt-6">
          <!-- Profile Info -->
          <v-window-item :value="0">
            <v-row class="form-grid" dense>
              <!-- Labels column -->
              <v-col cols="12" md="3" class="form-labels">
                <div class="form-label">Full Name</div>
                <div class="form-label">Email</div>
              </v-col>

              <!-- Inputs column -->
              <v-col cols="12" md="9" class="form-inputs">
                <div class="full-name-inputs">
                  <v-text-field
                    v-model="firstName"
                    placeholder="First name"
                    variant="outlined"
                    hide-details
                    density="comfortable"
                  />
                  <v-text-field
                    v-model="lastName"
                    placeholder="Last name"
                    variant="outlined"
                    hide-details
                    density="comfortable"
                  />
                </div>
                <v-text-field
                  v-model="email"
                  disabled
                  variant="outlined"
                  hide-details
                  density="comfortable"
                />
              </v-col>
            </v-row>

            <div v-if="isModified" class="button-row right-align">
              <v-btn
                variant="outlined"
                color="primary"
                class="rounded-pill px-6"
                @click="resetFields"
              >
                Cancel
              </v-btn>

              <v-btn
                :loading="loading"
                color="primary"
                class="rounded-pill px-6"
                @click="submit"
              >
                Save Changes
              </v-btn>
            </div>
          </v-window-item>

          <!-- Password Change -->
          <v-window-item :value="1">
            <form @submit.prevent="changePassword">
              <v-text-field
                v-model="currentPassword"
                label="Current Password"
                type="password"
                variant="outlined"
                class="mb-4"
                required
              />
              <v-text-field
                v-model="newPassword"
                :type="showPassword ? 'text' : 'password'"
                label="New Password"
                :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showPassword = !showPassword"
                variant="outlined"
                class="mb-4"
                required
              />
              <v-text-field
                v-model="confirmNewPassword"
                :type="showPassword ? 'text' : 'password'"
                label="Confirm New Password"
                :error="showPasswordMismatch"
                :error-messages="
                  showPasswordMismatch ? ['Passwords do not match'] : []
                "
                variant="outlined"
                class="mb-4"
                required
              />

              <v-btn
                :loading="changingPassword"
                :disabled="!passwordsMatch"
                color="primary"
                class="rounded-pill px-6"
                type="submit"
              >
                Change Password
              </v-btn>
            </form>
          </v-window-item>
        </v-window>

        <v-alert
          v-if="error"
          type="error"
          class="mt-4"
          variant="outlined"
          border="start"
        >
          {{ error }}
        </v-alert>

        <v-alert
          v-if="success"
          type="success"
          class="mt-4"
          variant="tonal"
          border="start"
        >
          {{ successMessage || 'Update successful!' }}
        </v-alert>
      </v-card>

      <!-- Logout -->
      <v-row justify="center" class="mt-6">
        <v-btn
          @click="logOut"
          color="primary"
          variant="flat"
          class="rounded-pill px-6 logout"
        >
          Logout
        </v-btn>
      </v-row>
    </v-container>
  </v-main>
</template>

<script>
import api from '@/axiosInstance'
import { auth } from '@/stores/auth'
import { useStudyStore } from '@/stores/study'

export default {
  name: 'UserProfile',
  data() {
    return {
      tab: 0,
      email: '',
      firstName: '',
      lastName: '',
      loading: false,
      error: '',
      success: false,
      successMessage: '',

      currentPassword: '',
      newPassword: '',
      confirmNewPassword: '',
      changingPassword: false,
      showPassword: false,

      originalFirstName: '',
      originalLastName: '',
    }
  },
  computed: {
    isModified() {
      return (
        this.firstName !== this.originalFirstName ||
        this.lastName !== this.originalLastName
      )
    },
    passwordsMatch() {
      return (
        this.newPassword === this.confirmNewPassword && this.newPassword !== ''
      )
    },
    showPasswordMismatch() {
      return (
        this.confirmNewPassword !== '' &&
        this.newPassword !== '' &&
        this.newPassword !== this.confirmNewPassword
      )
    },
  },
  mounted() {
    this.loadUserInfo()
  },
  methods: {
    resetFields() {
      this.loadUserInfo() // Re-fetches the original values
    },

    async loadUserInfo() {
      try {
        const res = await api.get('/accounts/get_user_profile_info')
        const user = res.data
        this.email = user.email
        this.firstName = user.first_name || ''
        this.lastName = user.last_name || ''
        this.originalFirstName = this.firstName
        this.originalLastName = this.lastName
      } catch (err) {
        this.error = 'Failed to load user profile.'
      }
    },
    async submit() {
      this.error = ''
      this.success = false
      this.loading = true
      try {
        const payload = {
          first_name: this.firstName,
          last_name: this.lastName,
        }
        const res = await api.post('/accounts/update_user_profile', payload)
        if (res.status === 200) {
          this.success = true
          this.successMessage = 'Profile updated successfully.'

          auth.user.first_name = this.firstName
          auth.user.last_name = this.lastName

          this.originalFirstName = this.firstName
          this.originalLastName = this.lastName
        }
      } catch (err) {
        this.error =
          err.response?.data?.error ||
          err.response?.data?.message ||
          'Failed to update profile.'
      } finally {
        this.loading = false
      }
    },
    async changePassword() {
      this.changingPassword = true
      this.error = ''
      this.success = false
      if (!this.passwordsMatch) {
        this.error = 'Passwords do not match.'
        this.changingPassword = false
        return
      }
      try {
        const res = await api.post('/accounts/change', {
          password: this.currentPassword,
          new_password: this.newPassword,
          new_password_confirm: this.confirmNewPassword,
        })
        if (res.status === 200) {
          this.success = true
          this.successMessage = 'Password changed successfully.'
          this.currentPassword = ''
          this.newPassword = ''
          this.confirmNewPassword = ''
        }
      } catch (err) {
        this.error =
          err.response?.data?.response?.errors?.[0] ||
          err.response?.data?.error ||
          'Failed to change password.'
      } finally {
        this.changingPassword = false
      }
    },
    async logOut() {
      try {
        const res = await api.post('/accounts/logout')
        if (res.status === 200) {
          auth.isAuthenticated = false
          auth.user = null
          const studyStore = useStudyStore()
          studyStore.reset()
          this.$router.push({ name: 'UserLogin' })
        }
      } catch (err) {
        console.error('Logout failed:', err)
      }
    },
  },
}
</script>

<style scoped>
<style scoped > .profile-page {
  max-width: 1000px;
  margin: auto;
  padding-top: 24px;
}

/* Banner */
.banner-container {
  position: relative;
  width: 100%;
  height: 220px;
  border-radius: 16px;
  margin-bottom: 80px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.banner-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 16px;
}

/* Avatar */
.avatar-wrapper {
  position: absolute;
  bottom: -60px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
}

.profile-avatar {
  border-radius: 50%;
  border: 4px solid white;
  background-color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.profile-avatar:hover {
  transform: scale(1.05);
}

/* Form Layout */
.form-grid {
  row-gap: 20px;
}

.form-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-weight: 500;
  font-size: 0.95rem;
  color: #444;
  gap: 24px;
  padding-top: 8px;
}

.form-inputs {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.full-name-inputs {
  display: flex;
  gap: 16px;
}

.full-name-inputs .v-text-field {
  flex: 1;
}

/* Buttons */
.button-row {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: flex-end;
}

.logout {
  margin-top: 16px;
  border-radius: 999px;
  padding: 10px 24px;
  font-weight: bold;
}
.v-alert {
  text-align: center;
  justify-content: center;
}
</style>
