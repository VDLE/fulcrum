<template>
  <v-dialog v-model="visible" persistent max-width="600">
    <v-card title="Facilitator Setup - Connect Tracking Tool">
      <v-card-text>
        <!-- Facilitator Instructions -->
        <v-alert
          type="info"
          variant="tonal"
          class="mb-4"
          icon="mdi-information"
        >
          Please download and run the local tracking tool and select a folder
          for storing results.
        </v-alert>

        <!-- Download btn for executable-->
        <v-btn
          class="mb-6"
          variant="tonal"
          color="primary"
          prepend-icon="mdi-download"
          @click="downloadTrackingTool()"
          :loading="isDownloading"
          :disabled="isDownloading"
          type="application/zip"
        >
          Download Tracking Tool
        </v-btn>

        <!-- Connection Checker-->
        <div class="d-flex align-center mb-3">
          <!-- No connection -->
          <v-progress-circular
            v-if="!isConnected"
            color="red"
            indeterminate
            class="me-3"
          ></v-progress-circular>
          <!-- Successful connection-->
          <v-progress-circular
            v-else
            color="green"
            model-value="100"
            class="me-3"
          ></v-progress-circular>
          <!-- Custome msg to pair with circles above -->
          <span>
            {{
              isConnected
                ? 'Tracking tool connected. Ready to begin!'
                : 'Waiting for connection to tracking tool...'
            }}
          </span>
        </div>
      </v-card-text>

      <!-- Action buttons-->
      <v-card-actions class="d-flex justify-space-between">
        <v-btn text="Exit" @click="leaveSession"></v-btn>
        <v-btn
          text="Begin"
          color="success"
          :disabled="!isConnected"
          @click="beginSession"
        ></v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import api from '@/axiosInstance'
export default {
  name: 'TrackingSetup',
  data() {
    return {
      isConnected: false,
      visible: true,
      pingRate: null,
      isDownloading: false,
    }
  },
  mounted() {
    this.startPinging()
  },
  beforeUnmount() {
    clearInterval(this.pingRate)
  },
  methods: {
    startPinging() {
      this.pingRate = setInterval(this.pingConnection, 5000) // Check for connection every 5 sec
    },

    async pingConnection() {
      try {
        const response = await fetch(
          'http://127.0.0.1:5001/check_local_tracking_running',
        )
        if (response.ok) {
          this.isConnected = true // Successful connection
          console.log('Tracking tool connected')
        } else {
          this.isConnected = false // Keep trying (Response, but not the right one)
        }
      } catch (err) {
        this.isConnected = false // Keep trying (Flask not found running)
      }
    },

    async downloadTrackingTool() {
      this.isDownloading = true
      try {
        const response = await api.post(
          '/download_tracking_tool',
          {},
          { responseType: 'blob' },
        )

        const blob = new Blob([response.data], { type: 'application/zip' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = 'FulcrumTrackingTool.zip'
        link.click()

        URL.revokeObjectURL(link.href)
      } catch (err) {
        console.error('Failed to download tracking tool', err)
      } finally {
        this.isDownloading = false
      }
    },

    async leaveSession() {
      this.visible = false
      this.$emit('quit')
    },

    async beginSession() {
      this.visible = false
      this.$emit('submit')
    },
  },
}
</script>
