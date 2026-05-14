import axios from 'axios'

const API_BASE_URL = '/api'
const DIRECT_API_URL = import.meta.env.VITE_DIRECT_API_URL || '/api'

// 1 minute cache lifetime
const CACHE_TTL = 60000
const cache = new Map()

function getApiClient(baseUrl = API_BASE_URL) {
  return axios.create({
    baseURL: baseUrl,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    responseType: 'json',
    maxContentLength: 50 * 1024 * 1024, // 50MB max
  })
}

// Basic error handler
const handleApiError = (error, operation) => {
  throw error
}

// Get cached data or fetch and cache new data
const getCachedData = async (key, fetchFn) => {
  const now = Date.now()
  const cachedItem = cache.get(key)

  if (cachedItem && now - cachedItem.timestamp < CACHE_TTL) {
    return cachedItem.data
  }

  try {
    const data = await fetchFn()
    cache.set(key, { data, timestamp: now })
    return data
  } catch (error) {
    throw error
  }
}

const apiClient = getApiClient()
const directApiClient = getApiClient(DIRECT_API_URL)

// Request interceptor for API calls
apiClient.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  },
)

// Response interceptor for API calls
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    return Promise.reject(error)
  },
)

let customBackendUrl = null
const setBackendUrl = url => {
  customBackendUrl = url
  cache.clear()
}

const retryApiCall = async (apiCall, maxRetries = 2, initialDelay = 300) => {
  let retryCount = 0
  let delay = initialDelay

  while (retryCount <= maxRetries) {
    try {
      return await apiCall()
    } catch (error) {
      // Don't retry if we've reached the max
      if (retryCount >= maxRetries) {
        throw error
      }

      // Don't retry certain errors like 401, 403, 404
      if (error.response && [401, 403, 404].includes(error.response.status)) {
        throw error
      }

      console.log(
        `Retrying API call (attempt ${retryCount + 1} of ${maxRetries})...`,
      )
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay))

      // Exponential backoff
      delay *= 2
      retryCount++
    }
  }
}

const makeApiCallWithFallback = async (path, options = {}) => {
  try {
    try {
      return await retryApiCall(() => apiClient.get(path, options))
    } catch (proxyError) {
      const directPath = path.startsWith('/') ? path : `/${path}`
      return await retryApiCall(() => directApiClient.get(directPath, options))
    }
  } catch (error) {
    throw error
  }
}

// Fallback empty data objects
const emptyStudyData = []

const emptySummaryMetrics = {
  participantCount: 0,
  avgCompletionTime: 0,
  metrics: [
    {
      title: 'Participants',
      value: 0,
      icon: 'mdi-account-group',
      color: 'primary',
    },
    {
      title: 'Avg Completion Time',
      value: '0s',
      icon: 'mdi-clock-outline',
      color: 'info',
    },
    {
      title: 'P-Value',
      value: 0.0,
      icon: 'mdi-function-variant',
      color: 'success',
    },
  ],
}

const emptyLearningCurve = []
const emptyTaskPerformance = []
const emptyParticipants = {
  data: [],
  pagination: {
    total: 0,
    page: 1,
    per_page: 20,
    pages: 0,
  },
}

const analyticsApi = {
  setBackendUrl,

  async getStudies() {
    // Clear cache to ensure fresh data
    cache.delete('studies')

    return getCachedData('studies', async () => {
      try {
        // Normal API call
        const response = await makeApiCallWithFallback('/analytics/studies')
        return response.data
      } catch (error) {
        return [...emptyStudyData]
      }
    })
  },

  async getSummaryMetrics(studyId) {
    return getCachedData(`summary_${studyId}`, async () => {
      try {
        // Try API call with fallback
        const response = await makeApiCallWithFallback(
          `/analytics/${studyId}/summary`,
        )
        return response.data
      } catch (error) {
        return emptySummaryMetrics
      }
    })
  },

  async getLearningCurveData(studyId) {
    return getCachedData(`learning_${studyId}`, async () => {
      try {
        // Try API call with fallback
        const response = await makeApiCallWithFallback(
          `/analytics/${studyId}/learning-curve`,
        )
        return response.data
      } catch (error) {
        return emptyLearningCurve
      }
    })
  },

  async getTaskPerformanceData(studyId) {
    return getCachedData(`tasks_${studyId}`, async () => {
      try {
        // Try API call with fallback
        const response = await makeApiCallWithFallback(
          `/analytics/${studyId}/task-performance`,
        )
        return response.data
      } catch (error) {
        return emptyTaskPerformance
      }
    })
  },

  async getParticipantData(studyId, page = 1, pageSize = 20) {
    return getCachedData(
      `participants_${studyId}_${page}_${pageSize}`,
      async () => {
        try {
          // Try API call with fallback
          const response = await makeApiCallWithFallback(
            `/analytics/${studyId}/participants`,
            {
              params: { page, pageSize },
            },
          )
          return response.data
        } catch (error) {
          return emptyParticipants
        }
      },
    )
  },

  async healthCheck() {
    try {
      // Try API call with fallback
      const response = await makeApiCallWithFallback('/analytics/health')
      return response.data
    } catch (error) {
      return {
        status: 'error',
        mode: 'empty',
        message: 'API connection failed, no data available',
      }
    }
  },

  async exportStudyData(studyId, format = 'csv') {
    try {
      // Validate format
      if (!['csv', 'json', 'xlsx'].includes(format)) {
        throw new Error(
          `Unsupported export format: ${format}. Must be csv, json, or xlsx.`,
        )
      }

      try {
        // For file downloads, we need different response type
        const options = {
          params: { format },
          responseType: 'blob',
        }

        // Try API call with fallback (custom handling for blob responses)
        try {
          const response = await apiClient.get(
            `/analytics/${studyId}/export`,
            options,
          )
          return response.data
        } catch (proxyError) {
          const response = await directApiClient.get(
            `/analytics/${studyId}/export`,
            options,
          )
          return response.data
        }
      } catch (error) {
        throw error
      }
    } catch (error) {
      handleApiError(error, `exportStudyData(${studyId}, ${format})`)
    }
  },

  async getTrialInteractionData(studyId, trialId) {
    return getCachedData(
      `trial_interaction_${studyId}_${trialId}`,
      async () => {
        try {
          // Try API call with fallback
          const response = await makeApiCallWithFallback(
            `/analytics/${studyId}/trial-interaction`,
            {
              params: { trial_id: trialId },
            },
          )
          return response.data
        } catch (error) {
          return {
            error: 'Failed to fetch trial interaction data',
            trialId: trialId,
            message: error.message,
          }
        }
      },
    )
  },

  async getParticipantTaskDetails(studyId, participantId) {
    return getCachedData(
      `participant_tasks_${studyId}_${participantId}`,
      async () => {
        try {
          // Try API call with fallback
          const response = await makeApiCallWithFallback(
            `/analytics/${studyId}/participant-task-details`,
            {
              params: { participant_id: participantId },
            },
          )
          return response.data
        } catch (error) {
          return []
        }
      },
    )
  },

  async getZipDataMetrics(studyId, participantId = null) {
    const cacheKey = participantId
      ? `zip_metrics_${studyId}_participant_${participantId}`
      : `zip_metrics_${studyId}`

    return getCachedData(cacheKey, async () => {
      try {
        // Set up params
        const params = {}
        if (participantId) {
          params.participant_id = participantId
        }

        // Request data from API (starts async process)
        const response = await makeApiCallWithFallback(
          `/analytics/${studyId}/zip-data`,
          {
            params,
          },
        )

        // Check if this is an async job (will have status="processing" and job_id)
        if (
          response.data &&
          response.data.status === 'processing' &&
          response.data.job_id
        ) {
          // Now we need to poll for results
          const jobId = response.data.job_id
          const maxAttempts = 60 // Max 60 attempts (with initial pollInterval of 1s)
          let attempts = 0
          let pollInterval = 1000 // Start with 1 second intervals

          // Define the polling function
          const pollForResults = async () => {
            attempts++

            try {
              // Check job status using our dedicated method
              const jobStatus = await this.checkJobStatus(jobId)

              if (jobStatus.status === 'completed') {
                // Job completed successfully
                return jobStatus.result
              } else if (jobStatus.status === 'failed') {
                // Job failed
                throw new Error(jobStatus.error || 'Processing failed')
              } else if (attempts >= maxAttempts) {
                // Too many attempts
                throw new Error('Timeout waiting for results')
              } else {
                // Job still in progress, wait and try again

                // Increasing poll interval with exponential backoff (max 5 seconds)
                pollInterval = Math.min(pollInterval * 1.2, 5000)

                // Wait for the interval then try again
                await new Promise(resolve => setTimeout(resolve, pollInterval))
                return pollForResults()
              }
            } catch (error) {
              if (attempts >= maxAttempts) {
                throw error
              }

              // Wait and try again
              await new Promise(resolve => setTimeout(resolve, pollInterval))
              return pollForResults()
            }
          }

          // Start polling
          return await pollForResults()
        } else {
          // Not an async job, return the data directly
          return response.data
        }
      } catch (error) {
        // Special handling for timeout errors
        if (error.message && error.message.includes('timeout')) {
          return {
            status: 'timeout',
            error:
              'Request timed out. The job may still be processing in the background.',
            message:
              'The server request timed out. Try checking the job status in a few seconds.',
            studyId: studyId,
            participantId: participantId,
          }
        }

        // Other errors
        return {
          error: 'Failed to fetch zip data metrics',
          studyId: studyId,
          participantId: participantId,
          message: error.message,
        }
      }
    })
  },

  async pollJobUntilComplete(
    jobId,
    maxAttempts = 60,
    initialPollInterval = 1000,
  ) {
    let attempts = 0
    let pollInterval = initialPollInterval

    while (attempts < maxAttempts) {
      attempts++
      try {
        // Check job status
        const jobStatus = await this.checkJobStatus(jobId)

        if (jobStatus.status === 'completed') {
          // Job is done
          return jobStatus.result
        } else if (jobStatus.status === 'failed') {
          // Job failed
          throw new Error(jobStatus.error || 'Job failed')
        } else if (jobStatus.status === 'not_found') {
          // Job not found
          throw new Error('Job not found')
        }

        // If we're here, job is still in progress (queued or running)
        // Wait before checking again
        await new Promise(resolve => setTimeout(resolve, pollInterval))

        // Increase poll interval with exponential backoff (max 5 seconds)
        pollInterval = Math.min(pollInterval * 1.2, 5000)
      } catch (error) {
        // For most errors, we should retry after waiting
        if (attempts >= maxAttempts) {
          throw new Error(
            `Polling timed out after ${maxAttempts} attempts: ${error.message}`,
          )
        }

        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, pollInterval))
        pollInterval = Math.min(pollInterval * 1.5, 5000) // Increase more aggressively on error
      }
    }

    // If we get here, we've run out of attempts
    throw new Error(`Polling timed out after ${maxAttempts} attempts`)
  },

  async checkJobStatus(jobId) {
    try {
      // Try API call with fallback
      const response = await makeApiCallWithFallback(`/analytics/jobs/${jobId}`)
      return response.data
    } catch (error) {
      return {
        job_id: jobId,
        status: 'error',
        error: error.message,
      }
    }
  },

  async getQueueStatus() {
    try {
      // Try API call with fallback
      const response = await makeApiCallWithFallback('/analytics/queue-status')
      return response.data
    } catch (error) {
      return {
        status: 'error',
        error: error.message,
      }
    }
  },

  async getParticipantMedia(studyId, participantId) {
    return getCachedData(`media_${studyId}_${participantId}`, async () => {
      try {
        const response = await makeApiCallWithFallback(
          `/analytics/participant-media/${studyId}/${participantId}`,
        )
        return response.data.trials || {}
      } catch (error) {
        return {}
      }
    })
  },

  getMediaFileUrl(studyId, participantId, trialId, filename) {
    return `/api/analytics/media/${studyId}/${participantId}/${trialId}/${filename}`
  },

  async getParticipantSurveys(studyId, participantId) {
    return getCachedData(`surveys_${studyId}_${participantId}`, async () => {
      try {
        const response = await makeApiCallWithFallback(
          `/analytics/participant-surveys/${studyId}/${participantId}`,
        )
        return response.data.surveys || { pre: null, post: null }
      } catch (error) {
        console.error('Error fetching participant surveys:', error)
        return { pre: null, post: null }
      }
    })
  },

  async getSurveyStructure(studyId) {
    return getCachedData(`survey_structure_${studyId}`, async () => {
      try {
        const response = await makeApiCallWithFallback(
          `/analytics/survey-structure/${studyId}`,
        )
        return response.data.structure || { pre: null, post: null }
      } catch (error) {
        console.error('Error fetching survey structure:', error)
        return { pre: null, post: null }
      }
    })
  },

  async getParticipantDemographics(studyId, participantId) {
    return getCachedData(
      `demographics_${studyId}_${participantId}`,
      async () => {
        try {
          const response = await makeApiCallWithFallback(
            `/analytics/participant-demographics/${studyId}/${participantId}`,
          )
          return response.data.demographics || null
        } catch (error) {
          console.error('Error fetching participant demographics:', error)
          return null
        }
      },
    )
  },
}

export default analyticsApi
