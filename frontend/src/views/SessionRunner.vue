<template>
  <v-main>
    <v-row>
      <v-col cols="12" md="10" offset-md="1">
        <v-progress-linear
          :model-value="progressTracker"
          height="10"
          color="primary"
          class="mb-6"
          striped
        />
      </v-col>
    </v-row>
    <v-container class="mt-5" v-if="currStepIndex != null">
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <!-- Facilitator Action Req to start Local Tracking -->
          <TrackingSetup
            v-if="
              currStepIndex <= 3 && trackingRequired && !trackingToolConnected
            "
            @submit="handleTrackingReady"
            @quit="exitSession"
          />

          <!-- Consent Ack (if applicable) -->
          <ConsentAckScreen
            v-if="currStepIndex == 0 && trackingToolConnected"
            :display="showConsentForm"
            @update:display="$emit('update:showConsentForm', $event)"
            :form="consentForm"
            :participantSessId="participantSessId"
            :studyId="sessionJson?.study_id"
            :liveSession="true"
            @submit="advanceNextStep"
          />

          <!-- Demographic Form (always) -->
          <DemographicForm
            v-if="currStepIndex == 1"
            :participantSessId="participantSessId"
            @submit="advanceNextStep"
          />

          <!-- Pre-survey Form (if applicable) -->
          <SessionSurvey
            v-if="showPreSurveyForm && currStepIndex == 2"
            :surveyJson="preSurveyForm"
            :participantSessId="participantSessId"
            survey_type="pre"
            @submit="advanceNextStep"
          />

          <!-- Tracking Phase using Fulcrum Tool -->
          <TrackingPhase
            v-if="currStepIndex == 3 && trackingRequired"
            :sessionParameters="sessionJson"
            @submit="advanceNextStep"
          />

          <!-- Post-survey Form (if applicable) -->
          <SessionSurvey
            v-if="showPostSurveyForm && currStepIndex == 4"
            :surveyJson="postSurveyForm"
            :participantSessId="participantSessId"
            survey_type="post"
            @submit="advanceNextStep"
          />

          <!-- Researcher Notes/Comments (always) -->
          <ResearcherNotes
            v-if="currStepIndex == 5"
            :participantSessId="participantSessId"
            @submit="exit"
          />
        </v-col>
      </v-row>
    </v-container>
  </v-main>
  <!-- Exit button -->
  <v-btn
    class="quit-btn mb-4"
    color="primary"
    variant="text"
    prepend-icon="mdi-arrow-left"
    @click="confirmExit"
  >
    Exit
  </v-btn>

  <!-- Confirmation Exit Dialog -->
  <v-dialog v-model="exitDialogVisible" max-width="400" persistent>
    <v-card
      title="Exit Session?"
      text="Are you sure you want to exit the session? Progress for the current step will not be saved."
    >
      <template v-slot:actions>
        <v-spacer></v-spacer>
        <v-btn @click="exitDialogVisible = false">Cancel</v-btn>
        <v-btn @click="exitSession">Confirm</v-btn>
      </template>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios'
import api from '@/axiosInstance'
import { useRouter } from 'vue-router'
import { useStudyStore } from '@/stores/study'
import TrackingSetup from '@/components/TrackingSetup.vue'
import ConsentAckScreen from '@/components/ConsentAckScreen.vue'
import DemographicForm from '@/components/DemographicForm.vue'
import SessionSurvey from '@/components/SessionSurvey.vue'
import TrackingPhase from '@/components/TrackingPhase.vue'
import ResearcherNotes from '@/components/ResearcherNotes.vue'

export default {
  components: {
    TrackingSetup,
    ConsentAckScreen,
    DemographicForm,
    SessionSurvey,
    TrackingPhase,
    ResearcherNotes,
  },

  setup() {
    const router = useRouter()
    const exit = () => {
      router.push({ name: 'UserStudies' })
    }
    return { exit }
  },

  data() {
    return {
      currStepIndex: null,
      participantSessId: null,
      sessionJson: null,
      trackingRequired: true, // Not true if they selected no measurement options for any of their tasks
      trackingToolConnected: false,
      exitDialogVisible: false,
      // Consent vars
      consentForm: null,
      hasConsentForm: false,
      showConsentForm: false,
      // Pre survey vars
      preSurveyForm: null,
      hasPreSurveyForm: false,
      showPreSurveyForm: false,
      // Post survey vars
      postSurveyForm: null,
      hasPostSurveyForm: false,
      showPostSurveyForm: false,
    }
  },

  async mounted() {
    this.participantSessId = useStudyStore().sessionID
  },

  watch: {
    async participantSessId(newVal) {
      if (!newVal) {
        console.warn('No participant session ID - redirecting')
        return this.exit()
      }

      await this.fetchSessionJson()
      if (!this.sessionJson?.study_id) {
        console.warn('Invalid session JSON - redirecting')
        return this.exit()
      }

      await this.fetchCurrentStep()
      await this.fetchForms()
      await this.checkSkipStep()
    },
  },

  computed: {
    progressTracker() {
      return Number.isInteger(this.currStepIndex)
        ? (this.currStepIndex / 6) * 100
        : 0
    },
  },

  methods: {
    // Move to next step in session workflow + save current step to db incase user wants to exit and come back later
    async advanceNextStep() {
      try {
        const response = await api.post('/update_current_session_step', {
          participant_session_id: this.participantSessId,
        })
        this.currStepIndex = response.data.current_step_index
      } catch (err) {
        console.error('Failed to update step:', err)
        return
      }

      await this.checkSkipStep()
    },

    // Certain steps are optional or dependent on what files were uploaded during study creation which we may need to skip past
    async checkSkipStep() {
      while (
        (this.currStepIndex === 0 && !this.hasConsentForm) ||
        (this.currStepIndex === 2 && !this.hasPreSurveyForm) ||
        (this.currStepIndex === 3 && !this.trackingRequired) ||
        (this.currStepIndex === 4 && !this.hasPostSurveyForm)
      ) {
        await this.advanceNextStep()
      }
    },

    handleTrackingReady() {
      this.trackingToolConnected = true
    },

    // Grabbing the json containing session details created & saved during Session Setup
    async fetchSessionJson() {
      try {
        const path = `/get_session_setup_json`
        const response = await api.post(path, {
          participant_session_id: this.participantSessId,
        })
        this.sessionJson = response.data

        // Check if they need our tracking tool or using their own stuff
        this.trackingRequired = Object.values(this.sessionJson.tasks).some(
          task => {
            return task.measurementOptions && task.measurementOptions.length > 0
          },
        )
        console.log('Tracking required?', this.trackingRequired)
      } catch (err) {
        console.error('Failed retrieving session JSON:', err)
      }
    },

    async fetchConsentForm() {
      try {
        const path = `/get_study_consent_form`
        const response = await api.post(
          path,
          { study_id: this.sessionJson.study_id },
          {
            responseType: 'blob',
          },
        )

        if (response.status === 200) {
          const fileName =
            response.headers['x-original-filename'] || 'consent_form.pdf'
          const blob = new File([response.data], fileName, {
            type: 'application/pdf',
          })
          this.consentForm = blob
          this.hasConsentForm = true
          if (this.currStepIndex == 0) {
            this.showConsentForm = true
          }
        } else if (response.status === 204) {
          this.hasConsentForm = false
          this.showConsentForm = false
        }
      } catch (err) {
        // Expected a consent form but failed to get it so still show ack dialog even if they cannot see the form
        console.warn('Error fetching consent form:', err)
        this.consentForm = null
        this.hasConsentForm = true // Supposed to but did not populate, but we can still get ack
        if (this.currStepIndex == 0) {
          this.showConsentForm = true
        }
      }
    },

    async fetchSurveyForm(survey_type) {
      try {
        const response = await api.post(
          '/get_study_survey_form',
          { study_id: this.sessionJson.study_id, survey_type: survey_type },
          { responseType: 'blob' },
        )
        if (response.status === 200) {
          const fileName =
            response.headers['x-original-filename'] ||
            `${survey_type}_survey_questionnaire.json`
          const file = new File([response.data], fileName, {
            type: 'application/json',
          })
          const text = await file.text()
          this[`${survey_type}SurveyForm`] = JSON.parse(text)

          if (survey_type == 'pre') {
            this.hasPreSurveyForm = true
            this.showPreSurveyForm = true
          } else if (survey_type == 'post') {
            this.hasPostSurveyForm = true
            this.showPostSurveyForm = true
          }
        } else if (response.status === 204) {
          if (survey_type == 'pre') {
            this.hasPreSurveyForm = false
            this.showPreSurveyForm = false
          } else if (survey_type == 'post') {
            this.hasPostSurveyForm = false
            this.showPostSurveyForm = false
          }
        }
      } catch (err) {
        if (err.response.status !== 204) {
          console.warn(`${survey_type} survey form retrieval failed:`, err)
        }
      }
    },

    async fetchForms() {
      await this.fetchConsentForm()
      await this.fetchSurveyForm('pre')
      await this.fetchSurveyForm('post')
    },

    // Allows us to know what step to start at if we are resuming an "in_progress" session currently
    async fetchCurrentStep() {
      try {
        const response = await api.post('/get_current_session_step', {
          participant_session_id: this.participantSessId,
        })
        this.currStepIndex = response.data.current_step_index
        console.log('Session Position:', this.currStepIndex)
      } catch (err) {
        console.error('Failed to retrieve step index:', err)
      }
    },
    confirmExit() {
      this.exitDialogVisible = true
    },

    // Must ensure tracking executable is closed when trying to exit since it can be running anytime between TrackingSetup and TrackingPhase steps
    async shutdownTrackingTool() {
      try {
        await axios.post(
          'http://127.0.0.1:5001/shutdown_local_tracking',
          { auth_key: 'shutdownOK' },
          { withCredentials: true },
        )
      } catch (err) {
        console.log('Tracking tool was already closed:', err)
      }
    },

    // Route back to User Studies Workspace & set the session ID so the Study Panel seeds open automatically
    async exitSession() {
      await this.shutdownTrackingTool()
      const studyStore = useStudyStore()
      studyStore.setDrawerStudyID(this.sessionJson?.study_id)
      studyStore.clearSessionID()
      this.$router.push({ name: 'UserStudies' })
    },
  },
}
</script>

<style scoped>
.btn-row {
  display: flex;
  margin-top: 50px;
}
.quit-btn {
  min-height: 40px;
  min-width: 200px;
}
</style>
