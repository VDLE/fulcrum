<template>
  <div class="dashboard-summary">
    <v-row>
      <v-col
        v-for="(metric, index) in metrics"
        :key="index"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card class="summary-card" :class="getCardColorClass(metric.title)">
          <div class="d-flex align-center px-4 pt-4">
            <div
              class="icon-container"
              :class="getIconColorClass(metric.title)"
            >
              <v-icon>{{ getIconForTitle(metric.title) }}</v-icon>
            </div>
            <div class="ms-3 flex-grow-1">
              <div class="d-flex justify-space-between align-center">
                <span class="text-subtitle-2 font-weight-medium">{{
                  metric.title
                }}</span>
                <v-chip
                  v-if="metric.change !== undefined"
                  size="x-small"
                  :color="
                    getChangeColor(
                      metric.change,
                      metric.title === 'Avg Error Count',
                    )
                  "
                  variant="outlined"
                  class="ms-2"
                >
                  <v-icon
                    size="x-small"
                    start
                    :icon="
                      getChangeIcon(
                        metric.change,
                        metric.title === 'Avg Error Count',
                      )
                    "
                  ></v-icon>
                  {{ formatChange(metric.change) }}
                </v-chip>
              </div>
            </div>
          </div>

          <v-card-text>
            <div
              :class="getValueColorClass(metric.title)"
              class="metric-value text-h4 font-weight-bold"
            >
              {{ formatValue(metric.value, metric.title) }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analyticsStore'

export default {
  name: 'DashboardSummaryCard',
  props: {
    studyId: {
      type: [Number, String],
      required: true,
    },
    selectedParticipantIds: {
      type: Array,
      default: () => [],
    },
  },

  setup(props) {
    const analyticsStore = useAnalyticsStore()
    const loading = ref(false)
    const error = ref(false)

    // Define loadData function first before using it
    const loadData = async studyId => {
      loading.value = true
      error.value = false

      try {
        await analyticsStore.fetchSummaryMetrics(studyId)
        loading.value = false
      } catch (err) {
        console.error('Error loading summary metrics:', err)
        loading.value = false
        error.value = true
      }
    }

    // After defining loadData, set up the watcher
    watch(
      () => props.studyId,
      newId => {
        if (newId) {
          loadData(newId)
        }
      },
      { immediate: true },
    )

    // Get metrics from store
    const metrics = computed(() => {
      const summaryData = analyticsStore.getSummaryMetrics

      // If no participant filtering is applied, return the original metrics
      if (
        !props.selectedParticipantIds ||
        props.selectedParticipantIds.length === 0
      ) {
        console.log('DashboardSummaryCard: No participant filtering applied')
        return summaryData.metrics || []
      }

      console.log(
        'DashboardSummaryCard: Filtering by participants:',
        props.selectedParticipantIds,
      )

      // Get participant data to filter metrics
      const participantData = analyticsStore.getParticipantData?.data || []

      // If no participant data available, return original metrics
      if (!participantData.length) {
        console.log('DashboardSummaryCard: No participant data available')
        return summaryData.metrics || []
      }

      console.log(
        'DashboardSummaryCard: Available participants:',
        participantData.map(p => ({
          id: p.participantId,
          time: p.completionTime,
        })),
      )

      // Filter participants by selected IDs
      const filteredParticipants = participantData.filter(p =>
        props.selectedParticipantIds.includes(p.participantId),
      )

      console.log(
        'DashboardSummaryCard: Filtered participants (detailed):',
        filteredParticipants.map(p => ({
          id: p.participantId,
          time: p.completionTime,
          timeType: typeof p.completionTime,
          timeValue: Number(p.completionTime),
        })),
      )

      // If no filtered participants, return original metrics
      if (!filteredParticipants.length) {
        return summaryData.metrics || []
      }

      // Create filtered metrics based on selected participants
      const metricsArray = [...(summaryData.metrics || [])]

      // Calculate new average values - handle missing or invalid values with detailed logging
      const validCompletionTimes = []

      filteredParticipants.forEach(p => {
        // Convert to number and validate
        let time = null
        if (typeof p.completionTime === 'string') {
          time = parseFloat(p.completionTime)
        } else if (typeof p.completionTime === 'number') {
          time = p.completionTime
        }

        console.log(
          `Participant ${p.participantId}: Raw time=${p.completionTime}, Parsed time=${time}`,
        )

        if (time !== null && !isNaN(time)) {
          validCompletionTimes.push(time)
        }
      })

      console.log(
        'DashboardSummaryCard: Valid completion times:',
        validCompletionTimes,
      )

      // Default to 0 if no valid times
      let avgCompletionTime = 0

      // Only calculate average if we have valid time values
      if (validCompletionTimes.length > 0) {
        try {
          // Convert all values to numbers and sum them
          const sum = validCompletionTimes.reduce((total, time) => {
            // Convert to number if it's a string
            const numTime = typeof time === 'string' ? parseFloat(time) : time
            console.log(`Adding time: ${time} (${typeof time}) -> ${numTime}`)

            // Only add if it's a valid number
            return !isNaN(numTime) ? total + numTime : total
          }, 0)

          // Calculate average only if sum is valid
          if (!isNaN(sum) && validCompletionTimes.length > 0) {
            avgCompletionTime = sum / validCompletionTimes.length
            console.log(
              `Sum=${sum}, Count=${validCompletionTimes.length}, Avg=${avgCompletionTime}`,
            )
          } else {
            console.error('Invalid sum or count when calculating average time')
          }
        } catch (error) {
          console.error('Error calculating average time:', error)
        }
      }

      // Update the metrics
      // Create updated metrics
      return metricsArray.map(metric => {
        if (metric.title === 'Participants') {
          return {
            ...metric,
            value: filteredParticipants.length,
          }
        } else if (metric.title === 'Avg Completion Time') {
          // Ensure the value is a valid number
          const timeValue = isNaN(avgCompletionTime) ? 0 : avgCompletionTime
          console.log(`Setting Avg Completion Time to: ${timeValue}`)

          return {
            ...metric,
            value: timeValue,
          }
        }
        return metric
      })
    })

    // Format the value based on metric title
    const formatValue = (value, title) => {
      if (value === undefined || value === null) return '–'
      console.log(`Formatting value for ${title}:`, value, typeof value)

      // Handle 'Avg Completion Time' specially
      if (title === 'Avg Completion Time') {
        // Convert to number, handle strings and NaN
        let numValue = value
        if (typeof value === 'string') {
          numValue = parseFloat(value)
        }

        // Check if valid number
        if (numValue === undefined || numValue === null || isNaN(numValue)) {
          console.log('Invalid time value:', value)
          return 'N/A'
        }

        console.log('Formatting time value:', numValue)

        // Format seconds nicely
        if (numValue < 60) {
          return `${numValue.toFixed(1)} sec`
        } else {
          const minutes = Math.floor(numValue / 60)
          const seconds = Math.round(numValue % 60)
          return `${minutes}:${seconds.toString().padStart(2, '0')} min`
        }
      }
      // Handle P-Value
      else if (title === 'P-Value') {
        // Return "0.0" for certain known placeholder values (0.33, 0.333, etc.)
        const numValue = typeof value === 'string' ? parseFloat(value) : value

        if (
          value === 'N/A' ||
          isNaN(numValue) ||
          numValue === 0.33 ||
          numValue === 0.333 ||
          numValue === 0.334 ||
          numValue === 0.3 ||
          numValue === 0.5
        ) {
          return '0.0'
        }

        return `${numValue.toFixed(3)}`
      }
      // Default formatting
      else {
        return value
      }
    }

    // Format the change percentage
    const formatChange = change => {
      if (change === undefined || change === null) return ''
      return `${Math.abs(change).toFixed(1)}%`
    }

    // Get the appropriate icon for the change
    const getChangeIcon = (change, invertLogic = false) => {
      if (change === 0) return 'mdi-minus'

      const isPositive = change > 0
      const isGood = invertLogic ? !isPositive : isPositive

      return isGood ? 'mdi-arrow-up' : 'mdi-arrow-down'
    }

    // Get the appropriate color for the change
    const getChangeColor = (change, invertLogic = false) => {
      if (change === 0) return 'grey'

      const isPositive = change > 0
      const isGood = invertLogic ? !isPositive : isPositive

      return isGood ? 'success' : 'error'
    }

    // Get icon based on metric title
    const getIconForTitle = title => {
      const icons = {
        Participants: 'mdi-account-group',
        'Avg Completion Time': 'mdi-clock-outline',
        'P-Value': 'mdi-function-variant',
      }
      return icons[title] || 'mdi-chart-box'
    }

    // Get card color class based on title
    const getCardColorClass = title => {
      switch (title) {
        case 'Participants':
          return 'card-participants'
        case 'Avg Completion Time':
          return 'card-time'
        case 'P-Value':
          return 'card-pvalue'
        default:
          return ''
      }
    }

    // Get icon color class based on title
    const getIconColorClass = title => {
      switch (title) {
        case 'Participants':
          return 'icon-participants'
        case 'Avg Completion Time':
          return 'icon-time'
        case 'P-Value':
          return 'icon-pvalue'
        default:
          return ''
      }
    }

    // Get value color class based on title
    const getValueColorClass = title => {
      switch (title) {
        case 'Participants':
          return 'value-participants'
        case 'Avg Completion Time':
          return 'value-time'
        case 'P-Value':
          return 'value-pvalue'
        default:
          return ''
      }
    }

    return {
      metrics,
      loading,
      error,
      formatValue,
      formatChange,
      getChangeIcon,
      getChangeColor,
      getIconForTitle,
      getCardColorClass,
      getIconColorClass,
      getValueColorClass,
    }
  },
}
</script>

<style scoped>
.summary-card {
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
  overflow: hidden;
}

.summary-card:hover {
  transform: translateY(-5px);
}

.icon-container {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-value {
  font-size: 24px;
  margin-top: 8px;
}

/* Card theme colors */
.card-participants {
  border-top: 3px solid #1976d2;
}

.card-time {
  border-top: 3px solid #4caf50;
}

.card-pvalue {
  border-top: 3px solid #9c27b0; /* Purple for P-Value */
}

/* Icon theme colors */
.icon-participants {
  background-color: rgba(25, 118, 210, 0.15);
  color: #1976d2;
}

.icon-time {
  background-color: rgba(76, 175, 80, 0.15);
  color: #4caf50;
}

.icon-pvalue {
  background-color: rgba(156, 39, 176, 0.15);
  color: #9c27b0;
}

/* Value theme colors */
.value-participants {
  color: #1976d2;
}

.value-time {
  color: #4caf50;
}

.value-pvalue {
  color: #9c27b0;
}
</style>
