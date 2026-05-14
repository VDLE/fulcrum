<template>
  <v-dialog v-model="visible" persistent class="consent-dialog">
    <template v-slot:default="{ isActive }">
      <v-card title="Participant Consent Agreement">
        <v-card-text>
          <pdf-app
            v-if="fileURL"
            :pdf="fileURL"
            style="height: 500px"
            :show-toolbar="true"
            :toolbar-options="{
              zoom: true,
              download: false,
              print: false,
              pager: true,
            }"
          >
          </pdf-app>
          <v-alert v-else type="error" variant="tonal"
            >Error loading consent form</v-alert
          >
        </v-card-text>
        <v-card-actions class="d-flex justify-space-between">
          <v-checkbox
            v-model="acknowledgeVal"
            label="I acknowledge"
          ></v-checkbox>
          <v-btn
            text="Continue"
            :disabled="!acknowledgeVal || saving"
            @click="onAcknowledge"
          ></v-btn>
        </v-card-actions>
      </v-card>
    </template>
  </v-dialog>
</template>
<script>
import PdfApp from 'vue3-pdf-app'
import api from '@/axiosInstance'

export default {
  name: 'ConsentAckScreen',
  components: {
    PdfApp,
  },
  props: {
    display: Boolean,
    form: {
      type: [Object, File, null],
      default: null,
    },
    // Only need the fields below for live sessions (not when displaying preview versions)
    participantSessId: {
      type: [Number, null],
      required: false,
    },
    studyId: {
      type: Number,
      required: false,
    },
    liveSession: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      acknowledgeVal: false,
      fileURL: null,
      saving: false,
    }
  },
  computed: {
    // Needed to avoid prop mutation
    visible: {
      get() {
        return this.display
      },
      set(newVal) {
        this.$emit('update:display', newVal)
      },
    },
  },
  mounted() {
    if (this.form instanceof File) {
      this.fileURL = URL.createObjectURL(this.form)
    }
  },
  watch: {
    form(newVal) {
      // Create new blob
      if (newVal instanceof File) {
        if (this.fileURL) {
          URL.revokeObjectURL(this.fileURL)
        }
        this.fileURL = URL.createObjectURL(newVal)
      } else if (!newVal && this.fileURL) {
        URL.revokeObjectURL(this.fileURL)
        this.fileURL = null
      }
    },
  },
  methods: {
    async onAcknowledge() {
      if (this.saving) {
        return
      }
      this.saving = true
      try {
        if (this.liveSession == true) {
          await this.saveConsentAck()
          this.$emit('submit')
        }
        this.$emit('update:display', false)
      } catch (err) {
        console.error('Consent save failed:', err)
      } finally {
        this.saving = false
      }
    },

    async saveConsentAck() {
      if (!this.participantSessId || !this.studyId) {
        return
      }
      try {
        const path = `/save_participant_consent`
        await api.post(path, {
          study_id: this.studyId,
          participant_session_id: this.participantSessId,
        })
      } catch (err) {
        console.error('Error saving consent ack:', err)
      }
    },
  },
}
</script>
<style scoped>
.consent-dialog {
  width: 60vw;
  max-width: 1500px;
  max-height: none;
}
</style>
