<template>
  <v-dialog v-model="dialog" width="800" class="participant-details-modal">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <div class="d-flex align-center">
          <span class="text-h5"
            >Participant {{ participant.sequentialNumber || participant.participantId }} Details</span
          >
        </div>
        <v-btn icon color="primary" @click="close" class="close-button">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text>
        <!-- Key metrics in card format -->
        <v-row class="mt-2">
          <v-col cols="12" md="4">
            <v-card outlined class="metric-card">
              <v-card-text class="d-flex align-center">
                <div class="avatar-circle mr-3">
                  <v-icon icon="mdi-account-circle" color="primary" size="large"></v-icon>
                </div>
                <div>
                  <div class="text-caption text-grey">Participant #</div>
                  <div class="text-h6">{{ participant.sequentialNumber || participant.participantId }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card outlined class="metric-card">
              <v-card-text class="d-flex align-center">
                <div class="avatar-circle mr-3">
                  <v-icon icon="mdi-timer" color="primary" size="large"></v-icon>
                </div>
                <div>
                  <div class="text-caption text-grey">
                    Average Completion Time
                  </div>
                  <div class="text-h6">
                    {{ formatTime(participant.completionTime) }}
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card outlined class="metric-card">
              <v-card-text class="d-flex align-center">
                <div class="avatar-circle mr-3">
                  <v-icon icon="mdi-clipboard-list" color="primary" size="large"></v-icon>
                </div>
                <div>
                  <div class="text-caption text-grey">Tasks Completed</div>
                  <div class="text-h6">{{ participant.trialCount || 0 }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Survey section -->
        <div class="mt-6">
          <h3 class="text-h5 mb-4">
            <v-icon start color="blue">mdi-clipboard-text</v-icon>
            Survey Responses
          </h3>

          <div v-if="isLoadingSurveys" class="text-center pa-4">
            <v-progress-circular
              indeterminate
              color="primary"
              size="32"
            ></v-progress-circular>
            <p class="mt-2">Loading survey data...</p>
          </div>

          <div v-else-if="surveyError" class="text-center">
            <v-icon color="error">mdi-alert-circle</v-icon>
            <p class="mt-2 text-body-1">{{ surveyError }}</p>
            <v-btn
              color="primary"
              @click="loadParticipantSurveys"
              class="mt-4"
              size="small"
            >
              <v-icon start>mdi-refresh</v-icon>
              Try Again
            </v-btn>
          </div>

          <participant-survey-view
            v-else
            :surveys="participantSurveys"
            :survey-structure="surveyStructure"
            :demographic="participantDemographics"
          ></participant-survey-view>
        </div>

        <!-- Media Section with Heat Map and Video -->
        <div v-if="mediaLoaded" class="mt-6">
          <h3 class="text-h5 mb-4">
            <v-icon start color="primary">mdi-image-multiple</v-icon>
            Participant Recordings
          </h3>

          <!-- Trials selector -->
          <v-select
            v-model="selectedTrial"
            :items="trialItems"
            label="Select Trial"
            item-title="title"
            item-value="id"
            outlined
            dense
            class="mb-4"
            @update:modelValue="handleTrialChange"
          ></v-select>

          <!-- Heatmap visualization -->
          <v-card variant="outlined" class="mb-4 pa-4">
            <div class="d-flex justify-space-between align-center mb-2">
              <h4 class="text-h6">
                <v-icon start color="orange">mdi-map</v-icon>
                Interaction Heatmap
              </h4>

              <v-btn
                v-if="selectedScreenshot"
                size="small"
                color="primary"
                variant="outlined"
                @click="openImageInNewTab"
              >
                <v-icon start>mdi-open-in-new</v-icon>
                View Full Size
              </v-btn>
            </div>

            <div
              v-if="selectedScreenshot"
              class="heatmap-container position-relative"
            >
              <img
                :src="
                  getMediaUrl(
                    participant.studyId,
                    participant.participantId,
                    selectedTrial,
                    selectedScreenshot,
                  )
                "
                class="heatmap-base"
                alt="Heatmap Base"
              />
              <!-- Heatmap overlay would be applied here -->
              <div class="heatmap-overlay"></div>
            </div>

            <div v-else class="text-center pa-6 grey lighten-4">
              <v-icon size="large" color="grey">mdi-image-off</v-icon>
              <p class="mt-2">No screenshots available for this trial</p>
            </div>
          </v-card>

          <!-- Video player -->
          <v-card variant="outlined" class="pa-4">
            <h4 class="text-h6 mb-2">
              <v-icon start color="red">mdi-video</v-icon>
              Session Recording
            </h4>

            <div v-if="selectedVideo" class="video-container">
              <video controls class="w-100 rounded">
                <source
                  :src="
                    getMediaUrl(
                      participant.studyId,
                      participant.participantId,
                      selectedTrial,
                      selectedVideo,
                    )
                  "
                  type="video/mp4"
                />
                Your browser does not support the video tag.
              </video>
            </div>

            <div v-else class="text-center pa-6 grey lighten-4">
              <v-icon size="large" color="grey">mdi-video-off</v-icon>
              <p class="mt-2">No video recording available for this trial</p>
            </div>
          </v-card>
        </div>

        <!-- Loading state -->
        <div v-else-if="isLoadingMedia" class="mt-6 text-center pa-4">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
          ></v-progress-circular>
          <p class="mt-4">Loading participant media...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="mediaError" class="mt-6 text-center">
          <v-icon color="error" size="64">mdi-alert-circle</v-icon>
          <p class="mt-2 text-body-1">{{ mediaError }}</p>
          <v-btn color="primary" size="small" @click="loadParticipantMedia" class="mt-4">
            <v-icon start>mdi-refresh</v-icon>
            Try Again
          </v-btn>
        </div>

        <!-- No media state -->
        <div v-else class="mt-6 text-center">
          <v-icon color="grey" size="64">mdi-chart-box-outline</v-icon>
          <p class="mt-2 text-grey-darken-1">
            No media files found for this participant.
          </p>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
import { ref, watch, onMounted, computed } from 'vue'
import analyticsApi from '@/api/analyticsApi'
import ParticipantSurveyView from './ParticipantSurveyView.vue'

export default {
  name: 'ParticipantDetailsModal',
  components: {
    ParticipantSurveyView,
  },
  props: {
    modelValue: {
      type: Boolean,
      default: false,
    },
    participant: {
      type: Object,
      default: () => ({
        participantId: '',
        studyId: '',
        completionTime: 0,
        trialCount: 0,
      }),
    },
  },
  setup(props, { emit }) {
    // Dialog state
    const dialog = computed({
      get: () => props.modelValue,
      set: value => emit('update:modelValue', value),
    })

    // Media loading state
    const isLoadingMedia = ref(false)
    const mediaError = ref(null)
    const participantMedia = ref({})
    const mediaLoaded = ref(false)

    // Survey loading state
    const isLoadingSurveys = ref(false)
    const surveyError = ref(null)
    const participantSurveys = ref({ pre: null, post: null })
    const surveyStructure = ref({ pre: null, post: null })
    const participantDemographics = ref(null)

    // Selected trial and media
    const selectedTrial = ref(null)
    const selectedScreenshot = ref(null)
    const selectedVideo = ref(null)

    // Computed properties
    const trialItems = computed(() => {
      if (!participantMedia.value) return []

      return Object.keys(participantMedia.value).map(trialId => ({
        id: trialId,
        title: `Trial ${trialId}`,
        screenshotCount:
          participantMedia.value[trialId]?.screenshots?.length || 0,
        videoCount: participantMedia.value[trialId]?.videos?.length || 0,
      }))
    })

    // Watch for dialog open to load media
    watch(
      () => props.modelValue,
      newVal => {
        if (
          newVal &&
          props.participant.studyId &&
          props.participant.participantId
        ) {
          loadParticipantMedia()
          loadParticipantSurveys()
        }
      },
    )

    // Watch for participant change
    watch(
      () => props.participant,
      newVal => {
        if (dialog.value && newVal.studyId && newVal.participantId) {
          loadParticipantMedia()
          loadParticipantSurveys()
        }
      },
      { deep: true },
    )

    // Load participant media
    const loadParticipantMedia = async () => {
      if (!props.participant.studyId || !props.participant.participantId) {
        mediaError.value = 'Missing study ID or participant ID'
        return
      }

      try {
        isLoadingMedia.value = true
        mediaError.value = null

        const media = await analyticsApi.getParticipantMedia(
          props.participant.studyId,
          props.participant.participantId,
        )

        participantMedia.value = media
        mediaLoaded.value = Object.keys(media).length > 0

        // Set initial selected trial if available
        if (mediaLoaded.value) {
          const firstTrialId = Object.keys(media)[0]
          selectedTrial.value = firstTrialId
          updateSelectedMedia(firstTrialId)
        }
      } catch (error) {
        console.error('Error loading participant media:', error)
        mediaError.value = 'Failed to load media files. Please try again.'
      } finally {
        isLoadingMedia.value = false
      }
    }

    // Handle trial change
    const handleTrialChange = trialId => {
      updateSelectedMedia(trialId)
    }

    // Update selected media based on trial
    const updateSelectedMedia = trialId => {
      if (!participantMedia.value[trialId]) return

      // Set first screenshot if available
      const screenshots = participantMedia.value[trialId].screenshots || []
      selectedScreenshot.value = screenshots.length > 0 ? screenshots[0] : null

      // Set first video if available
      const videos = participantMedia.value[trialId].videos || []
      selectedVideo.value = videos.length > 0 ? videos[0] : null
    }

    // Get URL for media file
    const getMediaUrl = (studyId, participantId, trialId, filename) => {
      return analyticsApi.getMediaFileUrl(
        studyId,
        participantId,
        trialId,
        filename,
      )
    }

    // Open image in new tab
    const openImageInNewTab = () => {
      if (!selectedScreenshot.value) return

      const url = getMediaUrl(
        props.participant.studyId,
        props.participant.participantId,
        selectedTrial.value,
        selectedScreenshot.value,
      )

      window.open(url, '_blank')
    }

    // Close the dialog
    const close = () => {
      dialog.value = false
    }

    // Format time display
    const formatTime = seconds => {
      if (!seconds) return 'N/A'

      // Ensure seconds is a number
      const numSeconds =
        typeof seconds === 'string' ? parseFloat(seconds) : seconds
      if (isNaN(numSeconds)) return 'N/A'

      // Format as seconds if very small
      if (numSeconds < 60) {
        return `${numSeconds.toFixed(1)} sec`
      }

      // Format as minutes and seconds if less than an hour
      if (numSeconds < 3600) {
        const minutes = Math.floor(numSeconds / 60)
        const remainingSeconds = Math.round(numSeconds % 60)
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')} min`
      }

      // Format as hours, minutes, and seconds
      const hours = Math.floor(numSeconds / 3600)
      const minutes = Math.floor((numSeconds % 3600) / 60)
      const remainingSeconds = Math.round(numSeconds % 60)
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')} hrs`
    }

    // Load survey structure
    const loadSurveyStructure = async () => {
      if (!props.participant.studyId) {
        return
      }

      try {
        const structure = await analyticsApi.getSurveyStructure(
          props.participant.studyId,
        )

        surveyStructure.value = structure
      } catch (error) {
        console.error('Error loading survey structure:', error)
      }
    }

    // Load participant demographics
    const loadParticipantDemographics = async () => {
      if (!props.participant.studyId || !props.participant.participantId) {
        return
      }

      try {
        const demographics = await analyticsApi.getParticipantDemographics(
          props.participant.studyId,
          props.participant.participantId,
        )

        participantDemographics.value = demographics
      } catch (error) {
        console.error('Error loading participant demographics:', error)
      }
    }

    // Load participant surveys
    const loadParticipantSurveys = async () => {
      if (!props.participant.studyId || !props.participant.participantId) {
        surveyError.value = 'Missing study ID or participant ID'
        return
      }

      try {
        isLoadingSurveys.value = true
        surveyError.value = null

        // Load surveys, structure, and demographics in parallel
        const [surveys] = await Promise.all([
          analyticsApi.getParticipantSurveys(
            props.participant.studyId,
            props.participant.participantId,
          ),
          loadSurveyStructure(),
          loadParticipantDemographics(),
        ])

        participantSurveys.value = surveys
      } catch (error) {
        console.error('Error loading participant surveys:', error)
        surveyError.value = 'Failed to load survey data. Please try again.'
      } finally {
        isLoadingSurveys.value = false
      }
    }

    return {
      dialog,
      close,
      formatTime,

      // Media loading
      isLoadingMedia,
      mediaError,
      participantMedia,
      mediaLoaded,
      loadParticipantMedia,

      // Survey loading
      isLoadingSurveys,
      surveyError,
      participantSurveys,
      surveyStructure,
      participantDemographics,
      loadParticipantSurveys,

      // Selected media
      selectedTrial,
      selectedScreenshot,
      selectedVideo,
      trialItems,

      // Media methods
      handleTrialChange,
      getMediaUrl,
      openImageInNewTab,
    }
  },
}
</script>

<style scoped>
.metric-card {
  height: 100%;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.task-card {
  height: 100%;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.avatar-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background-color: #E3F2FD;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button {
  position: absolute;
  top: 8px;
  right: 8px;
}

/* Media display styles */
.heatmap-container {
  width: 100%;
  max-height: 400px;
  overflow: hidden;
  border-radius: 4px;
  background-color: #f0f0f0;
  position: relative;
}

.heatmap-base {
  width: 100%;
  height: auto;
  display: block;
  max-height: 400px;
  object-fit: contain;
}

.heatmap-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  /* Overlay styling will be applied dynamically */
}

.video-container {
  width: 100%;
  max-height: 400px;
  overflow: hidden;
  border-radius: 4px;
  background-color: #000;
}

.video-container video {
  width: 100%;
  height: auto;
  max-height: 400px;
  display: block;
}
</style>
