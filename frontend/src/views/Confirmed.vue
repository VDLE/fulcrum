<template>
  <v-container
    class="d-flex justify-center align-center confirmed-container"
    fluid
  >
    <v-slide-y-transition mode="in-out">
      <v-card v-if="showCard" class="pa-8 confirmed-card" elevation="4">
        <div class="text-center">
          <h1 class="confirmed-title mb-4">Email Confirmation</h1>

          <p class="confirmed-message mb-4">
            <span v-if="isSuccess" class="success-icon">✅</span>
            {{ confirmationMessage }}
          </p>

          <p v-if="isSuccess" class="redirect-msg mt-4">
            Redirecting to
            <router-link to="/UserLogin" class="login-link">login</router-link>
            in {{ countdown }} seconds...
          </p>
        </div>
      </v-card>
    </v-slide-y-transition>
  </v-container>
</template>

<script>
export default {
  name: 'ConfirmedView',
  data() {
    return {
      confirmationMessage: '',
      isSuccess: false,
      countdown: 4,
      countdownTimer: null,
      showCard: false,
    }
  },
  created() {
    const success = this.$route.query.success
    const error = this.$route.query.error

    if (success) {
      this.isSuccess = true
      this.confirmationMessage = success
      this.startCountdown()
    } else if (error) {
      this.confirmationMessage = `⚠️ ${error}`
    } else {
      this.confirmationMessage = 'Email already confirmed'
    }
  },
  mounted() {
    this.showCard = true
  },
  methods: {
    startCountdown() {
      this.countdownTimer = setInterval(() => {
        if (this.countdown > 1) {
          this.countdown--
        } else {
          clearInterval(this.countdownTimer)
          this.$router.push('/UserLogin')
        }
      }, 1000)
    },
  },
  beforeUnmount() {
    if (this.countdownTimer) clearInterval(this.countdownTimer)
  },
}
</script>

<style scoped>
.confirmed-container {
  height: 100vh;
  background: linear-gradient(to right, #f5f7fa, #c3cfe2);
}

.confirmed-card {
  max-width: 500px;
  width: 100%;
  border-radius: 16px;
  text-align: center;
}

.confirmed-title {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
}

.confirmed-message {
  font-size: 1.2rem;
  color: #444;
}

.redirect-msg {
  font-size: 1rem;
  color: #555;
}

.success-icon {
  font-size: 1.8rem;
  margin-right: 0.5rem;
}

.login-link {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}
</style>
