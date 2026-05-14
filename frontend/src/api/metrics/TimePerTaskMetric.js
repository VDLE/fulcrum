import MetricStrategy from './MetricStrategy'

// Tracks how long tasks take to complete
export default class TimePerTaskMetric extends MetricStrategy {
  constructor(options = {}) {
    super()
    this.options = {
      aggregation: 'mean', // Options: mean, median, min, max
      ...options,
    }
  }

  // Calculate time metrics from task result data
  calculate(taskResults) {
    if (!Array.isArray(taskResults) || taskResults.length === 0) {
      return { overall: 0, byTask: {} }
    }

    // Group by task
    const taskGroups = {}
    taskResults.forEach(result => {
      const taskId = result.taskId || result.task_id
      if (!taskGroups[taskId]) {
        taskGroups[taskId] = []
      }

      // Only include successful tasks with valid times
      if (
        result.status === 'completed' &&
        typeof result.completionTime === 'number'
      ) {
        taskGroups[taskId].push(result.completionTime)
      }
    })

    // Calculate metrics for each task
    const byTask = {}
    let allTimes = []

    Object.entries(taskGroups).forEach(([taskId, times]) => {
      if (times.length > 0) {
        byTask[taskId] = this.aggregateValues(times)
        allTimes = allTimes.concat(times)
      } else {
        byTask[taskId] = 0
      }
    })

    // Calculate overall metric
    const overall = allTimes.length > 0 ? this.aggregateValues(allTimes) : 0

    return { overall, byTask }
  }

  // Helper to calculate stats based on chosen method
  aggregateValues(values) {
    if (values.length === 0) return 0

    switch (this.options.aggregation) {
      case 'mean':
        return values.reduce((sum, val) => sum + val, 0) / values.length

      case 'median':
        const sorted = [...values].sort((a, b) => a - b)
        const mid = Math.floor(sorted.length / 2)
        return sorted.length % 2 === 0
          ? (sorted[mid - 1] + sorted[mid]) / 2
          : sorted[mid]

      case 'min':
        return Math.min(...values)

      case 'max':
        return Math.max(...values)

      default:
        return values.reduce((sum, val) => sum + val, 0) / values.length
    }
  }

  // Get info about this metric
  getMetadata() {
    const aggName =
      this.options.aggregation.charAt(0).toUpperCase() +
      this.options.aggregation.slice(1)

    return {
      name: `${aggName} Time Per Task`,
      description: `${aggName} time taken to complete tasks`,
      unit: 'seconds',
    }
  }
}
