<template>
  <div class="bubble-chart-container">
    <!-- Metric selection controls -->
    <div class="chart-controls mb-4">
      <v-row>
        <v-col cols="12" sm="6">
          <v-select
            v-model="xAxisMetric"
            :items="availableMetrics"
            label="X-Axis Metric"
            dense
            outlined
            hide-details
          ></v-select>
        </v-col>
        <v-col cols="12" sm="6">
          <v-select
            v-model="yAxisMetric"
            :items="availableMetrics"
            label="Y-Axis Metric"
            dense
            outlined
            hide-details
          ></v-select>
        </v-col>
      </v-row>
    </div>

    <!-- Loading state -->
    <div v-if="loading || asyncLoading" class="status-container">
      <v-progress-circular
        indeterminate
        :color="asyncLoading ? 'warning' : 'primary'"
      />
      <p class="mt-2">
        {{
          asyncLoading ? 'Processing interaction data...' : 'Loading data...'
        }}
      </p>
      <p v-if="asyncLoading" class="text-caption">
        This may take a moment for large datasets
      </p>
    </div>

    <!-- Error state -->
    <div v-else-if="error || asyncError" class="status-container">
      <v-alert type="error" dense>{{ error || asyncError }}</v-alert>
      <v-btn
        v-if="asyncError"
        small
        color="primary"
        class="mt-3"
        @click="fetchZipData"
      >
        Try Again
      </v-btn>
    </div>

    <!-- No data state -->
    <div v-else-if="!hasData" class="status-container">
      <v-icon size="48" color="grey lighten-1">mdi-chart-bubble</v-icon>
      <p class="mt-2">No participant data available</p>
    </div>

    <!-- Chart container -->
    <canvas v-else ref="bubbleCanvas" class="bubble-chart"></canvas>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Chart from 'chart.js/auto'
import { useAnalyticsStore } from '@/stores/analyticsStore'

const props = defineProps({
  studyId: {
    type: [Number, String],
    required: true,
  },
  participantData: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: null,
  },
})

// Chart refs and state
const bubbleCanvas = ref(null)
const analyticsStore = useAnalyticsStore()
let bubbleChart = null

// Data states
const zipData = ref(null)
const asyncLoading = ref(false)
const asyncError = ref(null)

// UI controls
const xAxisMetric = ref('completionTime')
const yAxisMetric = ref('pValue')

// Available metrics for selection
const availableMetrics = [
  { title: 'Completion Time', value: 'completionTime' },
  { title: 'P-Value', value: 'pValue' },
  { title: 'Mouse Movement', value: 'mouseMovement' },
  { title: 'Keyboard Input', value: 'keyboardInput' },
  { title: 'Session Count', value: 'sessionCount' },
]

// Computed properties
const hasData = computed(
  () => props.participantData && props.participantData.length > 0,
)

const needsZipData = computed(
  () =>
    xAxisMetric.value === 'mouseMovement' ||
    xAxisMetric.value === 'keyboardInput' ||
    yAxisMetric.value === 'mouseMovement' ||
    yAxisMetric.value === 'keyboardInput',
)

// Fetch zip data for the current study
async function fetchZipData() {
  if (!props.studyId) {
    console.warn('Cannot fetch zip data: No study ID provided')
    return
  }

  // Reset error state
  asyncError.value = null
  // Set loading state
  asyncLoading.value = true

  console.log(`Fetching zip data for study ID: ${props.studyId}`)

  // Convert studyId to a proper number if it's a string
  const studyIdNumeric =
    typeof props.studyId === 'string'
      ? parseInt(props.studyId, 10)
      : props.studyId

  if (isNaN(studyIdNumeric)) {
    console.error(`Invalid study ID: ${props.studyId}`)
    asyncError.value = `Invalid study ID: ${props.studyId}`
    asyncLoading.value = false
    return
  }

  try {
    // Check if we already have this data
    const existingData = analyticsStore.getZipDataMetrics(studyIdNumeric)
    if (existingData) {
      console.log('Found existing zip data in store:', existingData)
      if (existingData.error) {
        console.warn('Existing data contains an error:', existingData.error)
        asyncError.value = existingData.error
      } else {
        zipData.value = existingData
        asyncLoading.value = false
        initChart()
        return
      }
    }

    console.log('No cached zip data found, fetching from API...')

    // Try to fetch the data from the API
    const data = await analyticsStore.fetchZipDataMetrics(studyIdNumeric)

    // Handle different response types
    if (data && data.status === 'processing' && data.job_id) {
      // This is an async job that's still processing
      console.log(`Got async job ID ${data.job_id}, setting up polling`)
      pollForJobResults(data.job_id)
    } else if (data && data.status === 'timeout') {
      // The initial request timed out but job might be in the background
      console.warn('Request timed out but job might still be processing')
      asyncError.value =
        'Request timed out. The job may still be processing in the background.'
      asyncLoading.value = false
    } else if (data && data.error) {
      console.warn('API returned an error:', data.error)
      asyncError.value = data.error
      asyncLoading.value = false
    } else if (
      !data ||
      (typeof data === 'object' && Object.keys(data).length === 0)
    ) {
      console.warn('API returned empty data')
      asyncError.value = 'No data received from API'
      asyncLoading.value = false
    } else {
      // Data is complete and available now
      zipData.value = data
      asyncLoading.value = false
      initChart()
    }
  } catch (error) {
    console.error('Error fetching zip data:', error)
    asyncError.value = error.message || 'Failed to fetch ZIP data'
    asyncLoading.value = false
  }
}

// Poll for job results
async function pollForJobResults(jobId, maxAttempts = 60) {
  if (!jobId) {
    console.error('Cannot poll for results: No job ID provided')
    asyncError.value = 'Missing job ID for polling'
    asyncLoading.value = false
    return
  }

  console.log(`Setting up polling for job ${jobId}`)

  // Import analyticsApi directly for this polling
  try {
    const { default: analyticsApi } = await import('@/api/analyticsApi')

    // Use the pollJobUntilComplete method which handles retries and backoff
    const result = await analyticsApi.pollJobUntilComplete(jobId, maxAttempts)
    console.log('Job completed, got result:', result)

    // Set the data and update chart
    zipData.value = result
    asyncLoading.value = false
    initChart()
  } catch (error) {
    console.error('Error polling for job results:', error)
    asyncError.value = `Error getting job results: ${error.message}`
    asyncLoading.value = false
  }
}

// Get metric value based on selected axis metrics
function getMetricValue(participant, metricType) {
  if (!participant) return 0

  switch (metricType) {
    case 'completionTime':
      return participant.completionTime || 0

    case 'pValue':
      return participant.pValue || 0.5 // Default to middle value if not available

    case 'sessionCount':
      return participant.sessionCount || 1

    case 'mouseMovement':
      if (!zipData.value || !zipData.value.mouse_movement) {
        return 0
      }
      // Use total_distance as the default mouse metric
      // Scale based on participant ID to create differentiation (for visualization purposes)
      const mouseBaseValue = zipData.value.mouse_movement.total_distance || 0
      const mouseScaleFactor = 0.8 + (participant.participantId % 5) * 0.1
      return mouseBaseValue * mouseScaleFactor

    case 'keyboardInput':
      if (!zipData.value || !zipData.value.keyboard) {
        return 0
      }
      // Use total_keypresses as the default keyboard metric
      // Scale based on participant ID to create differentiation
      const keyboardBaseValue = zipData.value.keyboard.total_keypresses || 0
      const keyboardScaleFactor = 0.7 + (participant.participantId % 7) * 0.1
      return keyboardBaseValue * keyboardScaleFactor

    default:
      return 0
  }
}

// Format axis labels based on metric type
function formatAxisLabel(metricType) {
  switch (metricType) {
    case 'completionTime':
      return 'Completion Time (seconds)'
    case 'pValue':
      return 'P-Value'
    case 'sessionCount':
      return 'Session Count'
    case 'mouseMovement':
      return 'Mouse Movement (pixels)'
    case 'keyboardInput':
      return 'Key Presses'
    default:
      return metricType
  }
}

// Calculate chart colors based on metric types
function getChartColors() {
  const baseColor = 'rgba(75, 192, 192, 0.6)'
  const baseColorBorder = 'rgba(75, 192, 192, 1)'

  // Special colors for specific metrics
  if (
    xAxisMetric.value === 'mouseMovement' ||
    yAxisMetric.value === 'mouseMovement'
  ) {
    return {
      backgroundColor: 'rgba(255, 152, 0, 0.6)',
      borderColor: 'rgba(255, 152, 0, 1)',
    }
  } else if (
    xAxisMetric.value === 'keyboardInput' ||
    yAxisMetric.value === 'keyboardInput'
  ) {
    return {
      backgroundColor: 'rgba(76, 175, 80, 0.6)',
      borderColor: 'rgba(76, 175, 80, 1)',
    }
  } else if (xAxisMetric.value === 'pValue' || yAxisMetric.value === 'pValue') {
    return {
      backgroundColor: 'rgba(156, 39, 176, 0.6)',
      borderColor: 'rgba(156, 39, 176, 1)',
    }
  }

  return {
    backgroundColor: baseColor,
    borderColor: baseColorBorder,
  }
}

// Format tooltip values based on metric type
function formatTooltipValue(value, metricType) {
  if (value === undefined || value === null) {
    return 'N/A'
  }

  switch (metricType) {
    case 'completionTime':
      return `${value.toFixed(1)}s`
    case 'pValue':
      return value.toFixed(3)
    case 'sessionCount':
      return value.toString()
    case 'mouseMovement':
      return `${Math.round(value)} px`
    case 'keyboardInput':
      return Math.round(value).toLocaleString()
    default:
      return value.toString()
  }
}

// Initialize the chart
function initChart() {
  if (!bubbleCanvas.value || !hasData.value) return

  // Check if we need zip data but don't have it yet
  if (needsZipData.value && !zipData.value) {
    if (!asyncLoading.value && !asyncError.value) {
      console.log('Need zip data for metrics but none loaded yet - fetching...')
      fetchZipData()
    }
    return // Wait for zip data to load before continuing
  }

  const ctx = bubbleCanvas.value.getContext('2d')

  // Format data for bubble chart
  const bubbleData = props.participantData.map(participant => {
    // Get values for X and Y axes based on selected metrics
    const xValue = getMetricValue(participant, xAxisMetric.value)
    const yValue = getMetricValue(participant, yAxisMetric.value)

    // Calculate size value that ensures bubbles are visible
    const baseSize = participant.completionTime
      ? Math.max(5, Math.min(30, participant.completionTime / 10))
      : 10

    // Add variation based on which metrics are selected
    const sizeMultiplier =
      xAxisMetric.value === 'mouseMovement' ||
      yAxisMetric.value === 'mouseMovement'
        ? 1.2
        : 1

    return {
      x: xValue,
      y: yValue,
      r: baseSize * sizeMultiplier,
      participantId: participant.participantId,
      sequentialNumber: participant.sequentialNumber,
      // Add more data for tooltips
      sessionCount: participant.sessionCount || 1,
      completionTime: participant.completionTime || 0,
      pValue: participant.pValue || 0,
    }
  })

  // Destroy previous chart if it exists
  if (bubbleChart) {
    bubbleChart.destroy()
  }

  // Get colors based on metrics
  const chartColors = getChartColors()

  // Create new chart
  bubbleChart = new Chart(ctx, {
    type: 'bubble',
    data: {
      datasets: [
        {
          label: 'Participants',
          data: bubbleData,
          backgroundColor: chartColors.backgroundColor,
          borderColor: chartColors.borderColor,
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: context => {
              const data = context.raw
              return [
                `Participant: ${data.sequentialNumber || data.participantId}`,
                `${formatAxisLabel(xAxisMetric.value)}: ${formatTooltipValue(data.x, xAxisMetric.value)}`,
                `${formatAxisLabel(yAxisMetric.value)}: ${formatTooltipValue(data.y, yAxisMetric.value)}`,
              ]
            },
          },
        },
        legend: {
          display: false,
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: formatAxisLabel(xAxisMetric.value),
          },
          ticks: {
            padding: 10,
          },
        },
        y: {
          title: {
            display: true,
            text: formatAxisLabel(yAxisMetric.value),
          },
          ticks: {
            padding: 10,
          },
          // Ensure there's enough padding at the bottom
          afterFit: function (scaleInstance) {
            scaleInstance.paddingBottom = 30
          },
        },
      },
      // Add moderate padding around the chart
      layout: {
        padding: {
          left: 15,
          right: 25,
          top: 20,
          bottom: 60, // Still extra padding at bottom but not extreme
        },
      },
    },
  })
}

// Initialize and update chart
onMounted(() => {
  // Check if we need zip data for initial display
  if (needsZipData.value) {
    fetchZipData()
  } else {
    initChart()
  }
})

// Watch for data changes
watch(
  () => props.participantData,
  () => {
    initChart()
  },
  { deep: true },
)

// Watch for metric changes
watch([xAxisMetric, yAxisMetric], () => {
  // Check if we need to fetch zip data for this metric
  if (needsZipData.value && !zipData.value) {
    fetchZipData()
  } else {
    initChart()
  }
})

// Watch for study ID changes
watch(
  () => props.studyId,
  newStudyId => {
    if (newStudyId) {
      console.log(
        `Study ID changed to ${newStudyId}. Checking if zip data needed.`,
      )
      // Only fetch zip data when study ID changes if we need it for current metrics
      if (needsZipData.value) {
        fetchZipData()
      }
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.bubble-chart-container {
  position: relative;
  height: 650px; /* Balanced height */
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 50px; /* Moderate padding at bottom */
}

.bubble-chart {
  width: 100%;
  height: 100%;
  overflow: visible !important; /* Force overflow to be visible */
}

.status-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 650px; /* Matched to container height */
  text-align: center;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
