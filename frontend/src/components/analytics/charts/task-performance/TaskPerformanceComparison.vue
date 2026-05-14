<template>
  <v-card>
    <v-card-title>
      <span class="chart-title">Task Performance Comparison</span>
      <!-- Tooltip for chart explanation -->
      <v-tooltip location="bottom">
        <template v-slot:activator="{ props }">
          <v-icon small class="ml-2" v-bind="props">
            mdi-information-outline
          </v-icon>
        </template>
        <span>Compares performance metrics across different tasks</span>
      </v-tooltip>
      <v-spacer></v-spacer>
      <!-- Toggle between different metrics -->
      <v-btn-toggle v-model="selectedMetric" mandatory>
        <v-btn small value="time" class="px-2">
          <v-icon x-small left>mdi-clock-outline</v-icon>
          Time
        </v-btn>
        <v-btn small value="pValue" class="px-2">
          <v-icon x-small left>mdi-function-variant</v-icon>
          P-Value
        </v-btn>
        <v-btn small value="mouse" class="px-2">
          <v-icon x-small left>mdi-mouse</v-icon>
          Mouse
        </v-btn>
        <v-btn small value="keyboard" class="px-2">
          <v-icon x-small left>mdi-keyboard</v-icon>
          Keys
        </v-btn>
      </v-btn-toggle>
    </v-card-title>

    <v-card-text>
      <div class="chart-container">
        <!-- Filter message when participants are selected -->
        <div
          v-if="selectedParticipantIds && selectedParticipantIds.length > 0"
          class="filter-message"
        >
          <v-chip color="primary" outlined size="small" class="mb-2">
            {{ filterMessage }}
          </v-chip>
        </div>

        <!-- Loading state - standard data loading -->
        <div v-if="loading" class="status-container">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-2">Loading data...</p>
        </div>

        <!-- Async loading state - for zip data operations -->
        <div v-else-if="asyncLoading" class="status-container">
          <v-progress-circular indeterminate color="warning" />
          <p class="mt-2">Processing interaction data...</p>
          <p class="text-caption">This may take a moment for large datasets</p>
        </div>

        <!-- Error state - API/database errors -->
        <div v-else-if="error" class="status-container">
          <v-alert type="error" dense>{{ error }}</v-alert>
        </div>

        <!-- Async error state - zip processing errors -->
        <div v-else-if="asyncError" class="status-container">
          <v-alert type="error" dense>{{ asyncError }}</v-alert>
          <v-btn small color="primary" class="mt-3" @click="fetchZipData">
            Try Again
          </v-btn>
        </div>

        <!-- Empty state -->
        <div v-else-if="!hasData" class="status-container">
          <v-icon size="48" color="grey lighten-1">mdi-chart-bar</v-icon>
          <p class="mt-2">No task performance data available</p>
        </div>

        <!-- D3 chart container with !important styles to force display -->
        <div
          v-else
          ref="chartContainer"
          class="chart-content"
          style="
            display: block !important;
            height: 400px !important;
            visibility: visible !important;
          "
        ></div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import ChartRenderer from './ChartRenderer'
import MetricProcessor from './MetricProcessor'
import { forceRender } from './forceRender'
import analyticsApi from '../../../../api/analyticsApi'

export default {
  name: 'TaskPerformanceComparison',
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
    participantTaskData: {
      type: Array,
      default: () => [],
    },
  },
  setup(props) {
    const selectedMetric = ref('time') // Default selected metric
    const chartContainer = ref(null)
    const resizeTimeout = ref(null)
    const validDataCount = ref(0) // Track how many valid data points we have
    const zipData = ref(null) // Will store zip data metrics when loaded
    const asyncError = ref(null) // Error message for async operations
    const asyncLoading = ref(false) // Loading state for async operations

    // Initialize the chart renderer
    const chartRenderer = new ChartRenderer({
      margin: { top: 40, right: 80, bottom: 120, left: 60 },
    })

    // Initialize the metric processor
    const metricProcessor = new MetricProcessor()

    // Check if we have data to display
    const hasData = computed(() => props.data && props.data.length > 0)

    // Filter and process the data based on selected participants
    const filteredData = computed(() => {
      if (!hasData.value) return []

      // If no participants are selected, use all data
      if (
        !props.selectedParticipantIds ||
        props.selectedParticipantIds.length === 0
      ) {
        return props.data
      }

      // Directly filter the data by participant ID if available
      const directFilteredData = props.data.filter(
        item =>
          item.participantId &&
          props.selectedParticipantIds.includes(item.participantId),
      )

      // If we have directly filtered data, use it
      if (directFilteredData.length > 0) {
        return directFilteredData
      }

      // Fallback to complex calculation for backward compatibility
      return metricProcessor.processParticipantData({
        data: props.data,
        participantTaskData: props.participantTaskData,
        selectedParticipantIds: props.selectedParticipantIds,
      })
    })

    // Get the appropriate label based on selected metric
    const metricLabel = computed(() => {
      switch (selectedMetric.value) {
        case 'time':
          return 'Avg Time (s)'
        case 'pValue':
          return 'Raw P-Value'
        case 'mouse':
          return 'Mouse Movement (px)'
        case 'keyboard':
          return 'Key Presses'
        default:
          return 'Avg Time (s)'
      }
    })

    // Check if we're showing data that requires zip files
    const needsZipData = computed(() => {
      return (
        selectedMetric.value === 'mouse' || selectedMetric.value === 'keyboard'
      )
    })

    // Display special message when filtering by participants
    const filterMessage = computed(() => {
      if (
        props.selectedParticipantIds &&
        props.selectedParticipantIds.length > 0
      ) {
        return `Showing data for ${props.selectedParticipantIds.length} selected participant(s)`
      }
      return ''
    })

    // Fetch zip data for mouse/keyboard metrics
    const fetchZipData = async () => {
      if (!props.studyId) {
        console.warn('Cannot fetch zip data: No study ID provided')
        return
      }

      // Reset error state
      asyncError.value = null
      // Set loading state
      asyncLoading.value = true

      // Initialize with empty structure that will be populated with real data
      zipData.value = {
        mouse_movement: {},
        keyboard: {},
        // For CSV integration during development (path to local test files)
        mouse_movement_csv: '/Task 1_mouse_movement_data.csv',
        keyboard_csv: '/Task 1_keyboard_data.csv'
      }

      console.log(`Fetching zip data for study ID: ${props.studyId}`)

      // Use the analytics API to get real data from CSVs

      // This initialization is already handled above
      
      // Load test CSV files directly (for development/testing)
      const loadTestCsvFiles = async () => {
        try {
          // Load mouse movement CSV
          const mouseResp = await fetch('/Task 1_mouse_movement_data.csv');
          const mouseText = await mouseResp.text();
          
          // Load keyboard CSV
          const keyboardResp = await fetch('/Task 1_keyboard_data.csv');
          const keyboardText = await keyboardResp.text();
          
          // Parse CSVs to arrays of objects
          const parseCSV = (csvText) => {
            const lines = csvText.split('\n');
            if (lines.length < 2) return [];
            
            const headers = lines[0].split(',');
            return lines.slice(1)
              .filter(line => line.trim())
              .map(line => {
                const values = line.split(',');
                return headers.reduce((obj, header, i) => {
                  obj[header] = values[i];
                  return obj;
                }, {});
              });
          };
          
          const mouseData = parseCSV(mouseText);
          const keyboardData = parseCSV(keyboardText);
          
          console.log(`Loaded test data: ${mouseData.length} mouse points, ${keyboardData.length} keypresses`);
          
          // Add parsed data to zipData
          zipData.value.mouse_movement_csv = mouseData;
          zipData.value.keyboard_csv = keyboardData;
          
          // Complete loading
          asyncLoading.value = false;
          updateChart();
        } catch (error) {
          console.error('Error loading test CSV files:', error);
          asyncError.value = `Failed to load test data: ${error.message}`;
          asyncLoading.value = false;
        }
      };
      
      // For testing/development, use local CSV files
      if (props.useTestData || props.studyId === 'test') {
        loadTestCsvFiles();
        return;
      }

      // Get real data from the API
      analyticsApi
        .getZipDataMetrics(props.studyId)
        .then(response => {
          // Check if there was an error
          if (response.error) {
            asyncError.value = `Failed to load interaction data: ${response.message || response.error}`
            console.error('Error fetching zip data:', response)
            asyncLoading.value = false
            return
          }

          // Check if we got a processing status (async job)
          if (response.status === 'processing' && response.job_id) {
            console.log(
              `Data processing in progress. Job ID: ${response.job_id}`,
            )

            // Set up polling for the job status
            const pollInterval = 2000 // 2 seconds between checks
            const maxAttempts = 30 // Maximum 1 minute of polling (30 * 2s)
            let attempts = 0

            const pollJobStatus = () => {
              attempts++
              analyticsApi
                .checkJobStatus(response.job_id)
                .then(statusResponse => {
                  if (statusResponse.status === 'completed') {
                    // Job completed successfully
                    // Process the result to ensure it has the expected format
                    const result = statusResponse.result
                    const processedData = zipData.value || {
                      mouse_movement: {},
                      keyboard: {},
                    }

                    // Handle if result is already in the expected format
                    if (result.mouse_movement) {
                      // Make a deep copy to ensure all properties are preserved
                      processedData.mouse_movement = {
                        ...result.mouse_movement,
                      }

                      // Explicitly look for important properties
                      if (result.mouse_movement.total_distance) {
                        console.log(
                          'Found mouse total_distance:',
                          result.mouse_movement.total_distance,
                        )
                        
                        // Save this value for future sessions
                        try {
                          localStorage.setItem('lastGoodMouseDistance', result.mouse_movement.total_distance.toString());
                        } catch (e) {
                          console.warn('Failed to save mouse data to localStorage:', e);
                        }
                      }
                    }
                    // Handle if mouse data is in a different format
                    else if (result.mouse_data || result.mouseData) {
                      processedData.mouse_movement = {
                        data: result.mouse_data || result.mouseData || [],
                      }
                    }

                    // Handle if result is already in the expected format
                    if (result.keyboard) {
                      // Make a deep copy to ensure all properties are preserved
                      processedData.keyboard = { ...result.keyboard }

                      // Explicitly look for important properties
                      if (result.keyboard.total_keypresses) {
                        console.log(
                          'Found keyboard total_keypresses:',
                          result.keyboard.total_keypresses,
                        )
                        
                        // Save this value for future sessions
                        try {
                          localStorage.setItem('lastGoodKeyPresses', result.keyboard.total_keypresses.toString());
                        } catch (e) {
                          console.warn('Failed to save keyboard data to localStorage:', e);
                        }
                      }
                    }
                    // Handle if keyboard data is in a different format
                    else if (result.keyboard_data || result.keyboardData) {
                      processedData.keyboard = {
                        data: result.keyboard_data || result.keyboardData || [],
                      }
                    }

                    // Process raw CSV data if available
                    if (result.raw_data && result.raw_data.mouse_movement) {
                      processedData.mouse_movement.data =
                        result.raw_data.mouse_movement
                    }

                    if (result.raw_data && result.raw_data.keyboard) {
                      processedData.keyboard.data = result.raw_data.keyboard
                    }

                    // Log raw job result structure for debugging
                    console.log('Raw job result:', result)

                    // Set processed data
                    zipData.value = processedData
                    console.log('Processed data structure:', processedData)

                    // Debug log for specific metrics we need
                    if (processedData.mouse_movement) {
                      console.log(
                        'Mouse data keys:',
                        Object.keys(processedData.mouse_movement),
                      )
                      const mouseNumericValues = Object.entries(
                        processedData.mouse_movement,
                      )
                        .filter(([_, val]) => typeof val === 'number')
                        .map(([key, val]) => `${key}: ${val}`)
                      console.log('Mouse numeric values:', mouseNumericValues)
                    }

                    if (processedData.keyboard) {
                      console.log(
                        'Keyboard data keys:',
                        Object.keys(processedData.keyboard),
                      )
                      const keyboardNumericValues = Object.entries(
                        processedData.keyboard,
                      )
                        .filter(([_, val]) => typeof val === 'number')
                        .map(([key, val]) => `${key}: ${val}`)
                      console.log(
                        'Keyboard numeric values:',
                        keyboardNumericValues,
                      )
                    }

                    // Copy over top-level properties that might be useful
                    if (result.total_data_points) {
                      processedData.total_data_points = result.total_data_points
                    }
                    if (result.data_types_found) {
                      processedData.data_types_found = result.data_types_found
                    }
                    if (result.avg_completion_time) {
                      processedData.avg_completion_time =
                        result.avg_completion_time
                    }
                    if (result.completion_times) {
                      processedData.completion_times = result.completion_times
                    }

                    // Update data with processed version
                    zipData.value = processedData
                    asyncLoading.value = false
                    updateChart()
                  } else if (statusResponse.status === 'failed') {
                    // Job failed
                    asyncError.value = `Processing failed: ${statusResponse.error || 'Unknown error'}`
                    asyncLoading.value = false
                  } else if (attempts >= maxAttempts) {
                    // Timeout
                    asyncError.value =
                      'Processing is taking longer than expected. Please try again later.'
                    asyncLoading.value = false
                  } else {
                    // Still processing, continue polling
                    setTimeout(pollJobStatus, pollInterval)
                  }
                })
                .catch(error => {
                  asyncError.value = `Error checking job status: ${error.message}`
                  asyncLoading.value = false
                })
            }

            // Start polling after a short delay
            setTimeout(pollJobStatus, pollInterval)
          } else {
            // Data is available immediately
            // Process the response to ensure it has the expected format
            const processedData = zipData.value || {
              mouse_movement: {},
              keyboard: {},
            }

            // Handle if response is already in the expected format
            // IMPORTANT: Make a deep copy of the object to preserve all properties
            if (response.mouse_movement) {
              processedData.mouse_movement = { ...response.mouse_movement }

              // Explicitly look for important properties
              if (response.mouse_movement.total_distance) {
                console.log(
                  'Found mouse total_distance:',
                  response.mouse_movement.total_distance,
                )
                
                // Save this value for future sessions
                try {
                  localStorage.setItem('lastGoodMouseDistance', response.mouse_movement.total_distance.toString());
                } catch (e) {
                  console.warn('Failed to save mouse data to localStorage:', e);
                }
              }
            }
            // Handle if mouse data is in a different format
            else if (response.mouse_data || response.mouseData) {
              processedData.mouse_movement = {
                data: response.mouse_data || response.mouseData || [],
              }
            }

            // Handle if response is already in the expected format
            if (response.keyboard) {
              // Make a deep copy to ensure all properties are preserved
              processedData.keyboard = { ...response.keyboard }

              // Explicitly look for important properties
              if (response.keyboard.total_keypresses) {
                console.log(
                  'Found keyboard total_keypresses:',
                  response.keyboard.total_keypresses,
                )
                
                // Save this value for future sessions
                try {
                  localStorage.setItem('lastGoodKeyPresses', response.keyboard.total_keypresses.toString());
                } catch (e) {
                  console.warn('Failed to save keyboard data to localStorage:', e);
                }
              }
            }
            // Handle if keyboard data is in a different format
            else if (response.keyboard_data || response.keyboardData) {
              processedData.keyboard = {
                data: response.keyboard_data || response.keyboardData || [],
              }
            }

            // Process raw CSV data if available
            if (response.raw_data && response.raw_data.mouse_movement) {
              processedData.mouse_movement.data =
                response.raw_data.mouse_movement
            }

            if (response.raw_data && response.raw_data.keyboard) {
              processedData.keyboard.data = response.raw_data.keyboard
            }

            // Log raw API response structure for debugging
            console.log('Raw API response:', response)

            // Set processed data
            zipData.value = processedData
            console.log('Processed data structure:', processedData)

            // Debug log for specific metrics we need
            if (processedData.mouse_movement) {
              console.log(
                'Mouse data keys:',
                Object.keys(processedData.mouse_movement),
              )
              const mouseNumericValues = Object.entries(
                processedData.mouse_movement,
              )
                .filter(([_, val]) => typeof val === 'number')
                .map(([key, val]) => `${key}: ${val}`)
              console.log('Mouse numeric values:', mouseNumericValues)
            }

            if (processedData.keyboard) {
              console.log(
                'Keyboard data keys:',
                Object.keys(processedData.keyboard),
              )
              const keyboardNumericValues = Object.entries(
                processedData.keyboard,
              )
                .filter(([_, val]) => typeof val === 'number')
                .map(([key, val]) => `${key}: ${val}`)
              console.log('Keyboard numeric values:', keyboardNumericValues)
            }

            // Copy over top-level properties that might be useful
            if (response.total_data_points) {
              processedData.total_data_points = response.total_data_points
            }
            if (response.data_types_found) {
              processedData.data_types_found = response.data_types_found
            }
            if (response.avg_completion_time) {
              processedData.avg_completion_time = response.avg_completion_time
            }
            if (response.completion_times) {
              processedData.completion_times = response.completion_times
            }

            // Update data with processed version
            zipData.value = processedData
            asyncLoading.value = false
            updateChart()
          }
        })
        .catch(error => {
          asyncError.value = `Failed to load interaction data: ${error.message}`
          console.error('Error fetching zip data:', error)
          asyncLoading.value = false
        })
    }

    // Initialize the chart
    const initChart = () => {
      if (!hasData.value || !chartContainer.value) return

      // Make sure container height is properly set for rendering
      chartContainer.value.style.height = '400px'

      // Apply aggressive force rendering techniques
      console.log(
        'Force rendering container:',
        forceRender(chartContainer.value),
      )

      // Initialize the chart with the container element
      chartRenderer.initChart(chartContainer.value)

      // Use setTimeout to ensure DOM has fully updated
      setTimeout(() => {
        // Apply force rendering again before update
        forceRender(chartContainer.value)

        updateChart()

        // Force more updates to ensure everything renders
        for (let i = 1; i <= 3; i++) {
          setTimeout(() => {
            console.log(`Force render attempt ${i}`)
            forceRender(chartContainer.value)
            window.dispatchEvent(new Event('resize'))
            updateChart()
          }, i * 200)
        }
      }, 100)
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
      if (needsZipData.value && (!zipData.value || !zipData.value.mouse_movement || Object.keys(zipData.value.mouse_movement).length === 0)) {
        if (!asyncLoading.value && !asyncError.value) {
          console.log(
            'Need zip data for metric but none loaded yet - fetching...',
          )
          asyncLoading.value = true;
          
          // Create empty structure for the data we'll need
          zipData.value = zipData.value || {};
          zipData.value.mouse_movement = zipData.value.mouse_movement || {};
          zipData.value.keyboard = zipData.value.keyboard || {};
          
          // Make the API call in the background
          fetchZipData().then(response => {
            // When the job completes, update the chart if needed
            if (response && !response.error) {
              console.log('Zip data fetch completed successfully');
              updateChart();
            }
          }).catch(e => {
            console.warn('Error fetching zip data:', e);
          }).finally(() => {
            // Clear loading state after a delay to ensure UI is responsive
            setTimeout(() => {
              asyncLoading.value = false;
              updateChart();
            }, 1000);
          });
        }
      }
      
      // If we need zip data and it's not fully available, ensure we have minimal structure
      if (needsZipData.value) {
        // Create minimal structure with fallback data if needed
        zipData.value = zipData.value || {};
        zipData.value.mouse_movement = zipData.value.mouse_movement || {};
        zipData.value.keyboard = zipData.value.keyboard || {};
        
        // Try to get values from localStorage as fallback
        try {
          const lastMouseDistance = localStorage.getItem('lastGoodMouseDistance');
          const lastKeyPresses = localStorage.getItem('lastGoodKeyPresses');
          
          if (lastMouseDistance && !zipData.value.mouse_movement.total_distance) {
            zipData.value.mouse_movement.total_distance = parseFloat(lastMouseDistance);
            console.log('Using fallback mouse distance from localStorage:', lastMouseDistance);
          }
          
          if (lastKeyPresses && !zipData.value.keyboard.total_keypresses) {
            zipData.value.keyboard.total_keypresses = parseInt(lastKeyPresses);
            console.log('Using fallback key presses from localStorage:', lastKeyPresses);
          }
        } catch (e) {
          console.warn('Failed to load fallback data from localStorage:', e);
        }
      }

      // For debugging - log the state of zipData
      if (needsZipData.value) {
        console.log('DEBUG - zipData state:', !!zipData.value);
        
        if (zipData.value) {
          if (selectedMetric.value === 'mouse') {
            console.log('  Mouse movement data:', !!zipData.value.mouse_movement);
            console.log('  Total distance:', zipData.value.mouse_movement?.total_distance);
          } else if (selectedMetric.value === 'keyboard') {
            console.log('  Keyboard data:', !!zipData.value.keyboard);
            console.log('  Total keypresses:', zipData.value.keyboard?.total_keypresses);
          }
        }
      }
      
      // We'll continue with chart rendering even if zipData isn't fully loaded
      // The MetricProcessor will handle undefined or incomplete data gracefully

      // Process the data with the selected metric
      const processedData = metricProcessor.processMetricData({
        data: filteredData.value,
        metric: selectedMetric.value,
        zipData: zipData.value,
      })

      // Track how many valid data points we have
      validDataCount.value = processedData.length

      // Render the chart
      chartRenderer.renderChart({
        data: processedData,
        metric: selectedMetric.value,
        container: chartContainer.value,
      })
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
    watch([() => props.data, filteredData], () => {
      updateChart()
    })

    // Special watch for metric changes
    watch(selectedMetric, newMetric => {
      // If switching to a metric that needs zip data
      if ((newMetric === 'mouse' || newMetric === 'keyboard') && needsZipData.value) {
        // Show async loading state temporarily
        asyncLoading.value = true;
        
        // Check if we need to fetch zip data
        if (!zipData.value) {
          // This will trigger the API call to get real data
          fetchZipData()
        } else {
          // We already have zip data, just need to update the chart
          asyncLoading.value = false;
        }
      } else {
        // For other metrics like time/pValue
        asyncLoading.value = false;
      }

      // Always update the chart
      updateChart()

      // If mouse or keyboard metrics are selected, force render the chart
      if (newMetric === 'mouse' || newMetric === 'keyboard') {
        // Use setTimeout to ensure DOM updates first
        setTimeout(() => {
          console.log(`Force rendering for ${newMetric} metric`)
          if (chartContainer.value) {
            forceRender(chartContainer.value)
            updateChart()

            // Multiple force renders for reliability
            setTimeout(() => {
              forceRender(chartContainer.value)
              updateChart()
              window.dispatchEvent(new Event('resize'))
              
              // Clear loading indicator after rendering is done
              asyncLoading.value = false;
              
              // Poll one more time to see if zip data has arrived
              setTimeout(() => {
                if (zipData.value && (
                    (newMetric === 'mouse' && !zipData.value.mouse_movement?.total_distance) ||
                    (newMetric === 'keyboard' && !zipData.value.keyboard?.total_keypresses)
                )) {
                  console.log('Checking for completed metrics job...');
                  analyticsApi.getZipDataMetrics(props.studyId)
                    .then(response => {
                      if (response && !response.error) {
                        console.log('Found completed metrics data!', response);
                        // Update zipData with new info
                        if (response.mouse_movement?.total_distance) {
                          zipData.value.mouse_movement.total_distance = response.mouse_movement.total_distance;
                          console.log('Updated mouse distance:', response.mouse_movement.total_distance);
                        }
                        if (response.keyboard?.total_keypresses) {
                          zipData.value.keyboard.total_keypresses = response.keyboard.total_keypresses;
                          console.log('Updated keyboard presses:', response.keyboard.total_keypresses);
                        }
                        // Force render update
                        updateChart();
                      }
                    })
                    .catch(err => console.warn('Error checking for updated metrics:', err));
                }
              }, 2000);
            }, 200)
          }
        }, 50)
      }
    })

    // Watch for study ID changes to fetch zip data if needed
    watch(
      () => props.studyId,
      newStudyId => {
        if (newStudyId && needsZipData.value) {
          console.log(
            `Study ID changed to ${newStudyId}. Checking if zip data needed.`,
          )
          fetchZipData()
        }
      },
      { immediate: true },
    )

    // Set up lifecycle hooks
    onMounted(() => {
      // Use nextTick to ensure DOM is fully rendered
      nextTick(() => {
        // Delay initialization slightly to ensure proper dimensions
        setTimeout(() => {
          initChart()

          // Force another update after a delay
          setTimeout(() => {
            updateChart()
            window.dispatchEvent(new Event('resize'))
          }, 300)
        }, 50)
      })

      // Listen for resize events
      window.addEventListener('resize', onResize)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', onResize)
      if (resizeTimeout.value) {
        clearTimeout(resizeTimeout.value)
      }
    })

    // Manual force render function for the button
    const manualForceRender = () => {
      console.log('Manual force render triggered')

      if (chartContainer.value) {
        // Force render with multiple approaches
        forceRender(chartContainer.value)

        // Force a complete chart redraw
        chartRenderer.resize(chartContainer.value)
        updateChart()

        // Dispatch multiple resize events to force reflow
        window.dispatchEvent(new Event('resize'))
        setTimeout(() => window.dispatchEvent(new Event('resize')), 100)
      }
    }

    return {
      selectedMetric,
      chartContainer,
      hasData,
      filteredData,
      metricLabel,
      needsZipData,
      zipData,
      asyncError,
      asyncLoading,
      validDataCount,
      filterMessage,
      fetchZipData,
      manualForceRender,
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
  height: 400px;
  position: relative;
  min-height: 400px;
}
</style>
