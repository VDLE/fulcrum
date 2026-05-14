<template>
  <v-container fluid>
    <!-- Study selector row -->
    <v-row>
      <v-col cols="12">
        <StudySelector @study-selected="onStudySelected" />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <!-- Loading state -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
        <p class="mt-4">Loading analytics data...</p>
      </v-col>
    </v-row>

    <!-- Error state -->
    <v-row v-else-if="error">
      <v-col cols="12">
        <v-alert type="error" variant="tonal">
          {{ errorMessage }}
          <template v-slot:append>
            <v-btn color="error" variant="text" @click="retryLoading">
              Retry
            </v-btn>
          </template>
        </v-alert>
      </v-col>
    </v-row>

    <!-- No study selected state -->
    <v-row v-else-if="!selectedStudy">
      <v-col cols="12" class="text-center pa-8">
        <v-icon icon="mdi-chart-box-outline" size="64" color="grey-lighten-1" />
        <h3 class="mt-4 text-grey-darken-1">Please select a study</h3>
        <p class="text-grey">
          Select a study from the dropdown above to view analytics
        </p>
      </v-col>
    </v-row>

    <!-- Analytics dashboard content -->
    <template v-else>
      <!-- Summary cards with DashboardSummaryCard and CustomFormulaInput in the same row -->
      <div class="chart-cards-container">
        <v-row>
          <!-- Regular metrics -->
          <v-col cols="12" md="9">
            <DashboardSummaryCard
              :study-id="selectedStudy"
              :selected-participant-ids="selectedParticipantIds"
            />
          </v-col>

          <!-- Custom Formula card -->
          <v-col cols="12" md="3">
            <CustomFormulaInput
              :study-id="selectedStudy"
              @formula-applied="onFormulaApplied"
            />
          </v-col>
        </v-row>
      </div>

      <!-- Charts section - Learning Curve and Task Performance in the same row -->
      <div class="chart-cards-container">
        <v-row class="mt-4">
          <!-- Learning curve chart -->
          <v-col cols="12" md="6">
            <v-card class="h-100">
              <v-card-title class="d-flex align-center">
                <v-icon icon="mdi-chart-line" class="me-2"></v-icon>
                Learning Curve
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <LearningCurveChart
                  :study-id="selectedStudy"
                  :data="learningCurveData"
                  :loading="loadingLearningCurve"
                  :error="learningCurveError"
                  :selected-participant-ids="selectedParticipantIds"
                />
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Task Performance chart -->
          <v-col cols="12" md="6">
            <v-card class="h-100">
              <v-card-title class="d-flex align-center">
                <v-icon icon="mdi-chart-bar" class="me-2"></v-icon>
                Task Performance
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <TaskPerformanceComparison
                  :study-id="selectedStudy"
                  :data="taskPerformanceData"
                  :loading="loadingTaskPerformance"
                  :error="taskPerformanceError"
                  :selected-participant-ids="selectedParticipantIds"
                />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Participant Comparison section - full width -->
      <div class="chart-cards-container">
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card style="height: auto; min-height: 700px; overflow: visible">
              <v-card-title class="d-flex align-center">
                <v-icon icon="mdi-chart-bubble" class="me-2"></v-icon>
                Participant Comparison
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text
                class="pa-1"
                style="height: calc(100% - 60px); overflow: visible"
              >
                <ParticipantBubbleChart
                  :study-id="selectedStudy"
                  :participantData="
                    selectedParticipants.length > 0
                      ? selectedParticipants
                      : participantData
                  "
                  :loading="loadingParticipants"
                  :error="participantsError"
                />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Participant data section -->
      <div class="chart-cards-container">
        <v-row class="mt-4">
          <v-col cols="12">
            <v-card>
              <v-card-title class="d-flex align-center">
                <v-icon icon="mdi-account-group" class="me-2"></v-icon>
                Participant Data
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <ParticipantTable
                  :study-id="selectedStudy"
                  :participants="participantData"
                  :loading="loadingParticipants"
                  :error="participantsError"
                  @selection-change="onParticipantSelectionChange"
                  @participants-selected="onParticipantsSelected"
                />
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Export options -->
      <v-row class="mt-4">
        <v-col cols="12" class="d-flex justify-end">
          <v-btn
            color="primary"
            prepend-icon="mdi-download"
            @click="exportData('csv')"
            class="me-2"
          >
            Export CSV
          </v-btn>
          <v-btn
            color="secondary"
            prepend-icon="mdi-code-json"
            @click="exportData('json')"
          >
            Export JSON
          </v-btn>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script>
import { ref, computed } from 'vue'
import { useAnalyticsStore } from '@/stores/analyticsStore'
import analyticsApi from '@/api/analyticsApi'

// Import analytics components
import StudySelector from '@/components/analytics/StudySelector.vue'
import DashboardSummaryCard from '@/components/analytics/DashboardSummaryCard.vue'
import LearningCurveChart from '@/components/analytics/LearningCurveChart.vue'
import TaskPerformanceComparison from '@/components/analytics/TaskPerformanceComparison.vue'
import ParticipantTable from '@/components/analytics/ParticipantTable.vue'
import ParticipantBubbleChart from '@/components/analytics/ParticipantBubbleChart.vue'
import CustomFormulaInput from '@/components/analytics/CustomFormulaInput.vue'

export default {
  components: {
    StudySelector,
    DashboardSummaryCard,
    LearningCurveChart,
    TaskPerformanceComparison,
    ParticipantTable,
    ParticipantBubbleChart,
    CustomFormulaInput,
  },

  setup() {
    const analyticsStore = useAnalyticsStore()
    const selectedStudy = ref(null)
    const loading = ref(false)
    const error = ref(false)
    const errorMessage = ref('')
    const customMetricResults = ref([])
    const selectedParticipantIds = ref([])
    const selectedParticipants = ref([])

    // Computed properties for accessing store data
    const learningCurveData = computed(
      () => analyticsStore.getLearningCurveData || [],
    )
    const loadingLearningCurve = computed(
      () => analyticsStore.isLoadingLearningCurve,
    )
    const learningCurveError = computed(
      () => analyticsStore.getLearningCurveError,
    )

    const taskPerformanceData = computed(
      () => analyticsStore.getTaskPerformanceData || [],
    )
    const loadingTaskPerformance = computed(
      () => analyticsStore.isLoadingTaskPerformance,
    )
    const taskPerformanceError = computed(
      () => analyticsStore.getTaskPerformanceError,
    )

    const participantData = computed(
      () => {
        const participants = analyticsStore.getParticipantData?.data || [];
        // Add sequential numbers to all participants
        return participants.map((participant, index) => ({
          ...participant,
          sequentialNumber: index + 1
        }));
      }
    )
    const loadingParticipants = computed(
      () => analyticsStore.isLoadingParticipants,
    )
    const participantsError = computed(
      () => analyticsStore.getParticipantsError,
    )

    const onStudySelected = async studyId => {
      console.log('Study selected:', studyId)
      selectedStudy.value = studyId
      if (studyId) {
        await loadStudyData(studyId)
      }
    }

    const onFormulaApplied = formula => {
      // Find if we already have this formula
      const existingIndex = customMetricResults.value.findIndex(
        m => m.key === formula.key,
      )

      if (existingIndex >= 0) {
        // Update existing entry
        customMetricResults.value[existingIndex] = formula
      } else {
        // Add new entry
        customMetricResults.value.push(formula)
      }

      console.log('Applied custom formula:', formula)
    }

    const loadStudyData = async studyId => {
      loading.value = true
      error.value = false

      try {
        // Load all required data for the study
        await Promise.all([
          analyticsStore.fetchSummaryMetrics(studyId),
          analyticsStore.fetchLearningCurve(studyId),
          analyticsStore.fetchTaskPerformance(studyId),
          analyticsStore.fetchParticipants(studyId),
        ])

        loading.value = false
      } catch (err) {
        console.error('Error loading analytics data:', err)
        loading.value = false
        error.value = true
        errorMessage.value = 'Failed to load analytics data. Please try again.'
      }
    }

    const retryLoading = () => {
      if (selectedStudy.value) {
        loadStudyData(selectedStudy.value)
      }
    }

    const exportData = async format => {
      if (!selectedStudy.value) return

      try {
        const blob = await analyticsApi.exportStudyData(
          selectedStudy.value,
          format,
        )
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute(
          'download',
          `study_${selectedStudy.value}_export.${format}`,
        )
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } catch (err) {
        console.error('Export failed:', err)
        // Display error notification
      }
    }

    // Handle participant selection changes
    const onParticipantSelectionChange = selectedIds => {
      console.log('DataAnalytics: Selected participant IDs:', selectedIds)

      // Ensure we're working with numbers for IDs
      selectedParticipantIds.value = selectedIds.map(id =>
        typeof id === 'string' ? parseInt(id, 10) : id,
      )

      console.log(
        'DataAnalytics: Updated selectedParticipantIds:',
        selectedParticipantIds.value,
      )
    }

    // Handle participants selected with full data
    const onParticipantsSelected = participants => {
      console.log(
        'DataAnalytics: Selected participants data:',
        participants.map(p => ({
          id: p.participantId,
          time: p.completionTime,
        })),
      )

      // Add sequential numbering to the participants data
      const participantsWithSequentialNumbers = participants.map((p, index) => ({
        ...p,
        sequentialNumber: index + 1
      }))

      selectedParticipants.value = participantsWithSequentialNumbers

      // Force a refresh of the computed properties that depend on selected participants
      // by making a shallow copy of the array
      selectedParticipantIds.value = [...selectedParticipantIds.value]
    }

    return {
      analyticsStore,
      selectedStudy,
      loading,
      error,
      errorMessage,
      customMetricResults,
      selectedParticipantIds,
      selectedParticipants,
      onStudySelected,
      onFormulaApplied,
      retryLoading,
      exportData,
      onParticipantSelectionChange,
      onParticipantsSelected,
      // Expose computed properties
      learningCurveData,
      loadingLearningCurve,
      learningCurveError,
      taskPerformanceData,
      loadingTaskPerformance,
      taskPerformanceError,
      participantData,
      loadingParticipants,
      participantsError,
    }
  },
}
</script>

<style scoped>
.v-card {
  height: 100%;
}

/* Add max-width constraint to charts for better readability */
.chart-cards-container {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
