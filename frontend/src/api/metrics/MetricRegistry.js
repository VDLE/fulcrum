import TimePerTaskMetric from './TimePerTaskMetric'
import CompletionRateMetric from './CompletionRateMetric'
import PValueMetric from './PValueMetric'

// Singleton registry for metrics
export default class MetricRegistry {
  constructor() {
    if (MetricRegistry.instance) {
      return MetricRegistry.instance
    }

    this.metrics = new Map()
    this.registerDefaultMetrics()

    MetricRegistry.instance = this
  }

  // Register built-in metrics
  registerDefaultMetrics() {
    // Time metrics with different aggregations
    this.register(
      'meanTimePerTask',
      new TimePerTaskMetric({ aggregation: 'mean' }),
    )
    this.register(
      'medianTimePerTask',
      new TimePerTaskMetric({ aggregation: 'median' }),
    )
    this.register(
      'minTimePerTask',
      new TimePerTaskMetric({ aggregation: 'min' }),
    )
    this.register(
      'maxTimePerTask',
      new TimePerTaskMetric({ aggregation: 'max' }),
    )

    // Other metrics
    this.register('completionRate', new CompletionRateMetric())
    this.register('pValue', new PValueMetric())
  }

  // Add metric to registry
  register(key, metric) {
    this.metrics.set(key, metric)
  }

  // Get metric by key
  getMetric(key) {
    return this.metrics.has(key) ? this.metrics.get(key) : null
  }

  // Calculate metric value
  calculate(key, data) {
    const metric = this.getMetric(key)
    return metric ? metric.calculate(data) : null
  }

  // Get all available metrics
  getAvailableMetrics() {
    const result = []
    this.metrics.forEach((metric, key) => {
      result.push({
        key,
        ...metric.getMetadata(),
      })
    })
    return result
  }
}
