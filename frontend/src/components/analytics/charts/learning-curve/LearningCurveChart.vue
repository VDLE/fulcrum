<template>
  <v-card>
    <v-card-title>
      <span class="chart-title">Learning Curve</span>
      <!-- Simple tooltip to explain the chart -->
      <v-tooltip location="bottom">
        <template v-slot:activator="{ props }">
          <v-icon small class="ml-2" v-bind="props">
            mdi-information-outline
          </v-icon>
        </template>
        <span>Shows how task completion time changes across attempts</span>
      </v-tooltip>
      <v-spacer></v-spacer>
      <!-- Toggle between all tasks view and individual tasks view -->
      <v-btn-toggle v-model="selectedView" mandatory class="me-2">
        <v-btn small value="all" class="px-2">
          <v-icon x-small left>mdi-chart-line</v-icon>
          All Tasks
        </v-btn>
        <v-btn small value="individual" class="px-2">
          <v-icon x-small left>mdi-chart-multiple</v-icon>
          By Task
        </v-btn>
      </v-btn-toggle>

      <!-- Toggle between different metrics -->
      <v-btn-toggle v-model="selectedMetric" mandatory>
        <v-btn small value="time" class="px-2">
          <v-icon x-small left>mdi-clock-outline</v-icon>
          Time
        </v-btn>
        <v-btn small value="mouse" class="px-2">
          <v-icon x-small left>mdi-mouse</v-icon>
          Mouse
        </v-btn>
        <v-btn small value="keyboard" class="px-2">
          <v-icon x-small left>mdi-keyboard</v-icon>
          Keyboard
        </v-btn>
      </v-btn-toggle>
    </v-card-title>

    <v-card-text>
      <div class="chart-container">
        <!-- Loading state -->
        <div v-if="loading" class="status-container">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-2">Loading data...</p>
        </div>

        <!-- Error state -->
        <div v-else-if="error" class="status-container">
          <v-alert type="error" dense>{{ error }}</v-alert>
        </div>

        <!-- Empty state -->
        <div v-else-if="!hasData" class="status-container">
          <v-icon size="48" color="grey lighten-1">mdi-chart-line</v-icon>
          <p class="mt-2">No learning curve data available</p>
        </div>

        <!-- D3 chart container -->
        <div v-else ref="chartContainer" class="chart-content"></div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import ChartRenderer from './ChartRenderer'
import DataProcessor from './DataProcessor'

export default {
  name: 'LearningCurveChart',
  props: {
    studyId: {
      type: [Number, String],
      required: true,
    },
    data: {
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
    selectedParticipantIds: {
      type: Array,
      default: () => [],
    },
  },
  setup(props) {
    const selectedView = ref('all')
    const selectedMetric = ref('time')
    const chartContainer = ref(null)
    const zipData = ref(null)
    const resizeTimeout = ref(null)

    // Initialize the chart renderer with configuration
    const chartRenderer = new ChartRenderer({
      margin: { top: 40, right: 80, bottom: 110, left: 60 },
    })

    // Initialize the data processor
    const dataProcessor = new DataProcessor()

    // Calculate if we have data to display
    const hasData = computed(() => props.data && props.data.length > 0)

    // Filter data based on selected participants
    const filteredData = computed(() => {
      if (!hasData.value) return []

      // If no participants are selected, use all data
      if (
        !props.selectedParticipantIds ||
        props.selectedParticipantIds.length === 0
      ) {
        return props.data
      }

      // Filter data to include only selected participants
      return props.data.filter(item =>
        props.selectedParticipantIds.includes(item.participantId),
      )
    })

    // Process the data based on selected view and metric
    const processedData = computed(() => {
      return dataProcessor.processData({
        data: filteredData.value,
        view: selectedView.value,
        metric: selectedMetric.value,
        zipData: zipData.value,
      })
    })

    // Fetch zip data for mouse/keyboard metrics
    const fetchZipData = async () => {
      console.log('Using hardcoded zip data for demo')

      // Create hardcoded data for demo purpose
      zipData.value = {
        mouse_movement: {
          total_distance: 42500,
          average_distance_per_task: 8500,
          average_clicks_per_task: 24,
          movement_patterns: {
            linear: 0.45,
            curved: 0.35,
            erratic: 0.2,
          },
        },
        keyboard: {
          total_keypresses: 870,
          average_keypresses_per_task: 174,
          most_used_keys: ['ctrl', 'a', 'delete', 'enter'],
          key_frequency: {
            navigation: 0.4,
            editing: 0.35,
            shortcuts: 0.25,
          },
        },
        scroll: {
          total_scroll_distance: 12800,
          average_scroll_per_task: 2560,
        },
      }

      // Wait a moment to simulate loading and then update the chart
      setTimeout(() => {
        updateChart()
      }, 500)
    }

    // Initialize the chart
    const initChart = () => {
      if (!hasData.value || !chartContainer.value) return

      // Initialize the chart with the container element
      chartRenderer.initChart(chartContainer.value)
      updateChart()
    }

    // Update the chart when data changes
    const updateChart = () => {
      if (
        !chartRenderer.isInitialized() ||
        !hasData.value ||
        !chartContainer.value
      )
        return

      // Check if we need zip data but don't have it yet
      if (
        (selectedMetric.value === 'mouse' ||
          selectedMetric.value === 'keyboard') &&
        !zipData.value
      ) {
        fetchZipData()
        return
      }

      // Render the chart based on the current view
      if (selectedView.value === 'all') {
        chartRenderer.renderAllTasksView({
          data: processedData.value,
          metric: selectedMetric.value,
          container: chartContainer.value,
        })
      } else {
        chartRenderer.renderIndividualTasksView({
          data: processedData.value,
          metric: selectedMetric.value,
          container: chartContainer.value,
        })
      }
    }

    // Handle window resize with debounce
    const onResize = () => {
      if (resizeTimeout.value) {
        clearTimeout(resizeTimeout.value)
      }

      resizeTimeout.value = setTimeout(() => {
        if (chartContainer.value) {
          // Rebuild chart
          chartRenderer.resize(chartContainer.value)
          updateChart()
        }
      }, 250)
    }

    // Watch for changes that require chart updates
    watch(
      [
        () => props.data,
        filteredData,
        processedData,
        selectedView,
        selectedMetric,
      ],
      () => {
        updateChart()
      },
    )

    // Watch for study ID changes to fetch zip data if needed
    watch(
      () => props.studyId,
      newStudyId => {
        if (newStudyId) {
          console.log(
            `Study ID changed to ${newStudyId}. Always fetching zip data now.`,
          )
          fetchZipData()
        }
      },
      { immediate: true },
    )

    // Set up lifecycle hooks
    onMounted(() => {
      initChart()
      window.addEventListener('resize', onResize)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', onResize)
      if (resizeTimeout.value) {
        clearTimeout(resizeTimeout.value)
      }
    })

    return {
      selectedView,
      selectedMetric,
      chartContainer,
      hasData,
      filteredData,
      fetchZipData,
      initChart,
      updateChart,
    }
  },
}
</script>

<style scoped>
.chart-title {
  font-weight: 500;
  font-size: 16px;
}

.chart-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.status-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  text-align: center;
}

.chart-content {
  width: 100%;
  height: 350px;
  position: relative;
  max-width: 900px;
  margin: 0 auto;
}
</style>
