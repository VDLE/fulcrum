import MetricStrategy from './MetricStrategy'

// Calculates p-value for significance testing
export default class PValueMetric extends MetricStrategy {
  // Calculates statistical significance (p-value)
  calculate(data) {
    if (!Array.isArray(data) || data.length === 0) {
      return { overall: 1.0, byTask: {} }
    }

    // Group data by task
    const taskGroups = {}
    data.forEach(result => {
      const taskId = result.taskId || result.task_id
      if (!taskGroups[taskId]) {
        taskGroups[taskId] = []
      }

      taskGroups[taskId].push(result)
    })

    // Calculate p-value for each task
    const byTask = {}
    let overallPValues = []

    Object.entries(taskGroups).forEach(([taskId, results]) => {
      // For demo purposes, use a simplistic p-value calculation
      // In a real implementation, this would use a proper statistical test
      const pValue = this.calculateSimplePValue(results)
      byTask[taskId] = pValue
      overallPValues.push(pValue)
    })

    // Average the p-values for overall significance
    const overall =
      overallPValues.length > 0
        ? overallPValues.reduce((sum, p) => sum + p, 0) / overallPValues.length
        : 1.0

    return { overall, byTask }
  }

  // Simple demo p-value calculation
  // In a real implementation, this would use a proper t-test or similar
  calculateSimplePValue(results) {
    if (results.length < 5) {
      return 0.5 // Not enough data for significance
    }

    // Get completion times
    const times = results.map(r => r.completionTime || r.completion_time || 0)

    if (times.length === 0) return 1.0

    // Calculate mean
    const mean = times.reduce((sum, t) => sum + t, 0) / times.length

    // Calculate standard deviation
    const squaredDiffs = times.map(t => Math.pow(t - mean, 2))
    const variance =
      squaredDiffs.reduce((sum, sq) => sum + sq, 0) / times.length
    const stdDev = Math.sqrt(variance)

    // Calculate standard error
    const stdError = stdDev / Math.sqrt(times.length)

    // Calculate t-statistic (against a hypothetical value)
    // For demo, we're testing if time is different from a threshold of 60 seconds
    const threshold = 60
    const tStat = Math.abs(mean - threshold) / stdError

    // Convert t-statistic to p-value (simplified approximation)
    // This is a very rough approximation for demonstration
    const pValue = 1 / (1 + Math.pow(tStat, 2))

    return pValue
  }

  // Returns info about this metric
  getMetadata() {
    return {
      name: 'P-Value',
      description: 'Statistical significance of results',
      unit: '',
    }
  }
}
