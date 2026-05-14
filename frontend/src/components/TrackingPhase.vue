<template>
  <v-main>
    <!-- Facilitator notice -->
    <v-alert type="info" variant="tonal" prominent class="mb-6">
      <strong> Facilitator Use Only</strong>
      Please ensure tracking tool is running before continuing.
    </v-alert>

    <!-- Connection status -->
    <v-alert v-if="!isConnected" type="error" class="mb-4" dense text
      >Please run the tracking tool before beginning.</v-alert
    >

    <div class="text-center mb-4">
      <h2 v-if="!attemptingToReconnect">
        {{ begunTracking ? 'In Progress...' : 'Ready to Start' }}
      </h2>
      <v-progress-circular
        v-else
        indeterminate
        color="warning"
        size="40"
        class="mb-4"
      />
      <p class="text-body-1 mb-6">
        {{
          attemptingToReconnect
            ? 'Attempting to reconnect to tracking tool...'
            : begunTracking
              ? formattedTimer
              : `Click "Begin" when ready. Minimize this window (DO NOT CLOSE) and open the external experiment application. Return to this screen and press "End" when finished.`
        }}
      </p>
    </div>

    <v-alert v-if="wrapUpFailed" type="error" variant="outlined" class="mb-4">
      Failed to save results. Please check the tracker and click Retry.
    </v-alert>

    <v-alert v-if="startError" type="error" variant="outlined" class="mb-4">
      {{ startError }}
    </v-alert>

    <v-row class="btn-row" justify="center">
      <!-- Begin button -->
      <v-btn
        v-if="!begunTracking"
        class="launcher-btn"
        :disabled="!isConnected"
        color="primary"
        @click="handleTrackingStart"
        >Begin</v-btn
      >

      <!-- Restart button-->
      <v-btn
        v-if="begunTracking && !resultsSaved"
        class="launcher-btn"
        :loading="isRestarting"
        :disabled="isWrappingUp || isRestarting"
        color="warning"
        @click="confirmRestart"
        >Restart Tracking</v-btn
      >

      <!-- End button -->
      <v-btn
        v-if="begunTracking && !resultsSaved && !wrapUpFailed"
        class="launcher-btn"
        :loading="isWrappingUp"
        :disabled="isWrappingUp || isRestarting || !isConnected"
        color="success"
        @click="handleWrapUpRequest"
        >End</v-btn
      >

      <!-- Retry button -->
      <v-btn
        v-if="wrapUpFailed && !resultsSaved"
        class="launcher-btn"
        color="error"
        @click="wrapUpTracking"
        >Retry</v-btn
      >

      <!-- Next button -->
      <v-btn
        v-if="resultsSaved"
        class="launcher-btn"
        color="secondary"
        @click="$emit('submit')"
        >Next</v-btn
      >
    </v-row>

    <v-dialog v-model="wrapUpConfirmDialogVisible" max-width="400" persistent>
      <v-card
        title="End Tracking?"
        text="Are you sure you want to end the tracking portion of this session?"
      >
        <template v-slot:actions>
          <v-spacer></v-spacer>
          <v-btn @click="wrapUpConfirmDialogVisible = false">Cancel</v-btn>
          <v-btn @click="wrapUpTracking">Confirm</v-btn>
        </template>
      </v-card>
    </v-dialog>

    <v-dialog v-model="wrapUpDialogVisible" max-width="600" persistent>
      <v-card
        title="Error Saving Results"
        text="Could not save session results. What would you like to do?"
      >
        <template v-slot:actions>
          <v-spacer></v-spacer>
          <v-btn @click="wrapUpTracking">Retry</v-btn>
          <v-btn @click="handleRestartFromFailure"
            >Restart From Beginning</v-btn
          >
          <v-btn @click="handleAdvanceAnyways">Advance Anyways</v-btn>
        </template>
      </v-card>
    </v-dialog>

    <v-dialog v-model="restartDialogVisible" max-width="400" persistent>
      <v-card
        title="Confirm Restart"
        text="Are you sure you want to restart this step from the beginning? Prior tracking data will not be saved, but can be found at the previously selected local directory."
      >
        <template v-slot:actions>
          <v-spacer></v-spacer>
          <v-btn @click="restartDialogVisible = false">Cancel</v-btn>
          <v-btn @click="restartTrackingPhase">Confirm</v-btn>
        </template>
      </v-card>
    </v-dialog>
  </v-main>
</template>

<script>
import axios from 'axios'
import api from '@/axiosInstance'

export default {
  name: 'TrackingPhase',
  emits: ['submit'],
  props: {
    sessionParameters: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      // Exe connection variables
      timer: 0,
      timerInterval: null,
      pingInterval: null,
      isConnected: true,
      attemptingToReconnect: false,
      reconnectTimer: null,
      reconnectTimeout: 5000,
      // UI state variables
      begunTracking: false,
      resultsReceived: false,
      resultsSaved: false,
      isWrappingUp: false,
      isRestarting: false,
      wrapUpFailed: false,
      startError: null,
      // Confirmation boxes
      wrapUpConfirmDialogVisible: false,
      wrapUpDialogVisible: false,
      restartDialogVisible: false,
      // Results
      zipRes: null,
      jsonRes: null,
    }
  },

  mounted() {
    this.startPinging()
  },

  beforeUnmount() {
    clearInterval(this.pingInterval)
    clearInterval(this.timerInterval)
    clearTimeout(this.reconnectTimer)
  },

  computed: {
    formattedTimer() {
      const mins = Math.floor(this.timer / 60)
        .toString()
        .padStart(2, '0')
      const secs = (this.timer % 60).toString().padStart(2, '0')
      return `${mins}:${secs}`
    },
  },

  methods: {
    startPinging() {
      clearInterval(this.pingInterval)

      this.pingConnection()
      this.pingInterval = setInterval(() => {
        this.pingConnection()
      }, 5000)
    },

    // Periodically checking if tracking executable is still running
    async pingConnection() {
      try {
        const response = await fetch(
          'http://127.0.0.1:5001/check_local_tracking_running',
        )
        const wasConnected = this.isConnected
        this.isConnected = response.ok

        if (!wasConnected && this.isConnected && this.begunTracking) {
          clearTimeout(this.reconnectTimer)
          this.attemptingToReconnect = false
          this.reconnectTimer = null
        }

        if (
          !this.isConnected &&
          this.begunTracking &&
          !this.attemptingToReconnect
        ) {
          this.startReconnectTimer()
        }
      } catch (err) {
        this.isConnected = false
        if (this.begunTracking && !this.attemptingToReconnect) {
          this.startReconnectTimer()
        }
      }
    },

    // Attempts to reconnect for a specified duration before concluding the connection is lost and should be restarted
    startReconnectTimer() {
      if (this.attemptingToReconnect) {
        return
      }
      this.attemptingToReconnect = true
      console.warn('Lost tracking connection, attempting to reconnect')
      this.reconnectTimer = setTimeout(() => {
        if (!this.isConnected && this.begunTracking) {
          console.error('Reconnect failed. Prompting restart...')
          this.confirmRestart()
        }
      }, this.reconnectTimeout)
    },

    // Response to when "begin" button is clicked
    async handleTrackingStart() {
      this.startError = null
      try {
        await this.sendParamsToTracker()
        this.begunTracking = true
        this.timerInterval = setInterval(() => {
          this.timer++
        }, 1000)
      } catch (err) {
        console.error('Tracker could not be started:', err)
        // /run_study returns 400 with {message, platform, supported} when the
        // measurements the study asks for aren't supported on the participant's
        // platform (e.g. Screen Recording on Linux/Wayland). Surface that text.
        const data = err.response?.data
        this.startError =
          data?.message ||
          data?.error ||
          'Tracker rejected the session. Confirm the local tracking tool is running.'
      }
    },

    // Sends session json to executable needed for automating the session + waking up the GUI toolbar
    async sendParamsToTracker() {
      const path = 'http://127.0.0.1:5001/run_study'
      const response = await api.post(path, this.sessionParameters, {
        withCredentials: true,
      })
      if (response.status !== 200)
        throw new Error('Tracker rejected session parameters JSON')
    },

    // Response to user clicking "End" button
    async handleWrapUpRequest() {
      if (this.resultsSaved || this.isWrappingUp) {
        return
      }
      this.wrapUpConfirmDialogVisible = true
    },

    // Upon confirming they wish to end, we need to fetch & save tracking data and signal the local flask to shutdown in the .exe
    async wrapUpTracking() {
      this.wrapUpConfirmDialogVisible = false
      this.isWrappingUp = true
      this.wrapUpFailed = false

      try {
        await this.waitForResultsReady()
        await this.fetchResults()
        await this.saveResults()
        // Best-effort: tell the local agent to drop its local ZIP copy.
        // Not awaited as a hard dependency. If it 500s or networks out,
        // we still consider the session saved successfully.
        this.cleanupLocalResults().catch(err =>
          console.warn('Local cleanup failed (non-fatal):', err),
        )
        await this.shutdownTrackingTool()
        clearInterval(this.timerInterval)
        clearInterval(this.pingInterval)
      } catch (err) {
        this.wrapUpFailed = true
        this.wrapUpDialogVisible = true
        clearInterval(this.pingInterval)
      } finally {
        this.isWrappingUp = false
      }
    },

    // Poll the local agent until the session ZIP is packaged and ready to fetch.
    // Without this, /get_session_zip_results 404s if the browser asks before the
    // participant finishes ending the trial run in the Qt toolbar.
    async waitForResultsReady() {
      const intervalMs = 500
      const timeoutMs = 60000
      const deadline = Date.now() + timeoutMs
      while (Date.now() < deadline) {
        try {
          const resp = await axios.get(
            'http://127.0.0.1:5001/session_results_status',
          )
          const { state, message } = resp.data || {}
          if (state === 'ready') return
          if (state === 'error') {
            throw new Error(
              message || 'Local tracker reported a packaging error',
            )
          }
        } catch (err) {
          // Network blip mid-poll: keep retrying until deadline.
          if (err.message && err.message.startsWith('Local tracker')) throw err
        }
        await new Promise(r => setTimeout(r, intervalMs))
      }
      throw new Error(
        'Timed out waiting for local tracker to finish packaging results',
      )
    },

    // Trigger confirmation to the user's request to restart this portion of the session
    async confirmRestart() {
      this.restartDialogVisible = true
    },

    // Provide the option to restart if connection could not be salvaged when trying to end
    async handleRestartFromFailure() {
      this.wrapUpDialogVisible = false
      this.restartDialogVisible = true
    },

    // All logic for handling a full restart of the tracking portion (reset states)
    async restartTrackingPhase() {
      this.restartDialogVisible = false
      this.isRestarting = true
      clearTimeout(this.reconnectTimer)
      this.attemptingToReconnect = false
      this.reconnectTimer = null

      try {
        await this.shutdownTrackingTool()
      } catch (err) {
        console.error('Shutdown failed or tracker not running', err)
      }

      clearInterval(this.pingInterval)
      clearInterval(this.timerInterval)

      //Reset variables
      this.timer = 0
      this.begunTracking = false
      this.resultsReceived = false
      this.resultsSaved = false
      this.isWrappingUp = false
      this.isRestarting = false
      this.attemptingToReconnect = false
      this.reconnectTimer = null
      this.wrapUpFailed = false
      this.isConnected = true

      this.startPinging()
    },

    // Retrieve the zip with participant data and finalized json for sending to the server flask
    async fetchResults() {
      try {
        // Fetching results
        const zipResponse = await axios.get(
          'http://127.0.0.1:5001/get_session_zip_results',
          {
            responseType: 'blob',
          },
        )
        this.zipRes = zipResponse.data

        const jsonResponse = await axios.get(
          'http://127.0.0.1:5001/get_session_json_results',
        )

        if (!jsonResponse.data || typeof jsonResponse.data !== 'object') {
          throw new Error('Invalid or missing JSON results')
        }
        this.jsonRes = jsonResponse.data

        this.resultsReceived = true
      } catch (err) {
        console.error('Failed to fetch session results:', err)
        throw err
      }
    },

    // Sending zip + finalized json to server
    async saveResults() {
      try {
        const formData = new FormData()
        const file = new File([this.zipRes], 'session_results.zip', {
          type: 'application/zip',
        })
        formData.append('file', file)
        formData.append('json', JSON.stringify(this.jsonRes))

        await api.post('/save_participant_session', formData, {
          headers: {},
          transformRequest: [data => data],
        })
        this.resultsSaved = true
      } catch (err) {
        console.error('Failed to save session results:', err)
        throw err
      }
    },

    // After the backend has accepted the upload, the local copy is no longer
    // needed. Asks the local agent to delete its ZIP so ~/.fulcrum/sessions/
    // doesn't accumulate stale data.
    async cleanupLocalResults() {
      await axios.post(
        'http://127.0.0.1:5001/cleanup_session_results',
        {},
        { withCredentials: true },
      )
    },

    // Signaling the .exe to shutdown safely & quietly
    async shutdownTrackingTool() {
      try {
        await axios.post(
          'http://127.0.0.1:5001/shutdown_local_tracking',
          { auth_key: 'shutdownOK' },
          { withCredentials: true },
        )
      } catch (err) {
        console.error('Failed to shutdown local tracking:', err)
      }
    },

    // Saving failed but giving the option to forcefully advance to next steps anyways
    async handleAdvanceAnyways() {
      this.wrapUpDialogVisible = false
      this.resultsSaved = true // Not actually but we are allowing user to continue forward for the time being
      try {
        await this.shutdownTrackingTool()
      } catch (err) {
        console.error(
          'Shutdown failed after Advance-Anyways-Button clicked',
          err,
        )
      }
    },
  },
}
</script>

<style scoped>
.launcher-wrapper {
  max-width: 600px;
  margin: 0 auto;
}
.btn-row {
  display: flex;
  margin-top: 50px;
}
.launcher-btn {
  min-height: 40px;
  min-width: 200px;
}
</style>
