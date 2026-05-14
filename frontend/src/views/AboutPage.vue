<template>
  <v-main>
    <v-container class="mt-5 about-page">
      <!-- Header -->
      <v-card class="header-card mb-8" elevation="4">
        <v-row align="center">
          <v-col cols="auto">
            <v-icon color="white" size="48">mdi-lightbulb-on-outline</v-icon>
          </v-col>
          <v-col>
            <h2 class="white--text mb-1">Welcome to Fulcrum</h2>
            <p class="white--text">
              Your all-in-one platform for HCI research studies
            </p>
          </v-col>
        </v-row>
      </v-card>

      <!-- Mission Statement -->
      <v-card class="pa-6 mb-8" elevation="2">
        <h3 class="text-h6 font-weight-bold mb-4">Why Fulcrum?</h3>
        <p class="mb-3">
          Conducting HCI research today often means stitching together multiple
          platforms for study creation, data collection, analytics, and session
          management.
        </p>
        <p class="mb-3">
          <strong>Fulcrum</strong> streamlines this experience by offering a
          single, flexible web-based interface that centralizes every step of
          the process.
        </p>
        <v-divider class="my-4" />
        <v-row>
          <v-col cols="12" md="4">
            <v-icon size="36" color="primary">mdi-pencil-ruler</v-icon>
            <h4 class="text-subtitle-1 font-weight-medium mt-2">
              Study Builder
            </h4>
            <p>Create and configure multi-phase studies in minutes.</p>
          </v-col>
          <v-col cols="12" md="4">
            <v-icon size="36" color="primary">mdi-database-search</v-icon>
            <h4 class="text-subtitle-1 font-weight-medium mt-2">
              Data Collection
            </h4>
            <p>Built-in support for capturing behavioral and biometric data.</p>
          </v-col>
          <v-col cols="12" md="4">
            <v-icon size="36" color="primary">mdi-chart-box-outline</v-icon>
            <h4 class="text-subtitle-1 font-weight-medium mt-2">
              Integrated Analytics
            </h4>
            <p>Visualize and export data directly from the platform.</p>
          </v-col>
        </v-row>
      </v-card>

      <!-- Developer Team -->
      <v-card class="pa-6 mb-8" elevation="2">
        <h3 class="text-h6 font-weight-bold mb-4">Meet the Team</h3>
        <v-row>
          <v-col cols="12" md="4" v-for="dev in developers" :key="dev.name">
            <v-card class="pa-3" elevation="1">
              <v-avatar size="48">
                <img
                  :src="dev.avatar"
                  :alt="`Avatar for ${dev.name}`"
                  class="avatar-img"
                />
              </v-avatar>
              <h4 class="text-subtitle-1 font-weight-medium">{{ dev.name }}</h4>
            </v-card>
          </v-col>
        </v-row>
        <p class="mt-4 text-caption">
          Advisors: Vinh Le & Levi Scully<br />
          Project for the University of Nevada, Reno - Department of Computer
          Science and Engineering
        </p>
      </v-card>

      <!-- Call to Action -->
      <v-card class="cta-card pa-6" elevation="4">
        <v-row align="center">
          <v-col>
            <h3 class="text-h6 font-weight-bold mb-1">Ready to get started?</h3>
            <p v-if="!auth.isAuthenticated">
              Create an account. All you need is an email.
            </p>
            <p v-else>You’re all set! Start by creating your first study.</p>
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="primary"
              class="rounded-pill px-6"
              elevation="2"
              @click="handleCTA"
            >
              {{ auth.isAuthenticated ? 'Create a Study' : 'Sign Up' }}
              <v-icon end>mdi-arrow-right</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card>
    </v-container>
  </v-main>
</template>

<script>
import { auth } from '@/stores/auth'
import { useStudyStore } from '@/stores/study'
export default {
  name: 'AboutPage',
  setup() {
    const studyStore = useStudyStore()
    return { studyStore, auth }
  },
  data() {
    return {
      developers: [
        {
          name: 'Nicholas Jarvis',
          avatar: '/images/view at your own leisure.jpg',
        },
        {
          name: 'Brandon Rowell',
          avatar: '/images/Nevada-Wolf-Pack-football-logo.jpg',
        },
        {
          name: 'Heather Z.',
          avatar: '/images/Nevada-Wolf-Pack-football-logo.jpg',
        },
      ],
    }
  },
  methods: {
    handleCTA() {
      if (this.auth.isAuthenticated) {
        this.studyStore.clearStudyID()
        sessionStorage.removeItem('currentStudyID')
        this.studyStore.incrementFormResetKey()
        this.$router.push({ name: 'StudyForm' })
      } else {
        this.$router.push({ name: 'UserRegister' })
      }
    },
  },
}
</script>

<style scoped>
.about-page {
  max-width: 1000px;
  margin: auto;
}

.header-card {
  background: linear-gradient(90deg, #1976d2 0%, #42a5f5 100%);
  color: white;
  padding: 24px;
  border-radius: 16px;
}

.cta-card {
  background-color: #e3f2fd;
  border: 2px dashed #90caf9;
  border-radius: 16px;
}

.avatar-img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}
</style>
