import MetricStrategy from './MetricStrategy'

// Calculates task completion rates
export default class CompletionRateMetric extends MetricStrategy {
  // Takes task results and calculates completion percentages
  calculate(taskResults) {
    if (!Array.isArray(taskResults) || taskResults.length === 0) {
      return { overall: 0, byTask: {} }
    }

    // Group by task
    const taskGroups = {}
    taskResults.forEach(result => {
      const taskId = result.taskId || result.task_id
      if (!taskGroups[taskId]) {
        taskGroups[taskId] = {
          total: 0,
          completed: 0,
        }
      }

      taskGroups[taskId].total++
      if (result.status === 'completed') {
        taskGroups[taskId].completed++
      }
    })

    // Calculate completion rate for each task
    const byTask = {}
    let totalCompleted = 0
    let totalTasks = 0

    Object.entries(taskGroups).forEach(([taskId, counts]) => {
      byTask[taskId] =
        counts.total > 0 ? (counts.completed / counts.total) * 100 : 0
      totalCompleted += counts.completed
      totalTasks += counts.total
    })

    // Calculate overall completion rate
    const overall = totalTasks > 0 ? (totalCompleted / totalTasks) * 100 : 0

    return { overall, byTask }
  }

  // Returns info about this metric
  getMetadata() {
    return {
      name: 'Task Completion Rate',
      description: 'Percentage of tasks successfully completed',
      unit: '%',
    }
  }
}
