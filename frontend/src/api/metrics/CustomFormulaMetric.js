import MetricStrategy from './MetricStrategy'

// Lets users create custom metric calculations
export default class CustomFormulaMetric extends MetricStrategy {
  // Setup a custom metric with a user-defined formula
  constructor(options) {
    super()

    if (typeof options.formula !== 'function') {
      throw new Error('CustomFormulaMetric requires a formula function')
    }

    this.formula = options.formula
    this.metadata = {
      name: options.name || 'Custom Metric',
      description:
        options.description || 'Custom metric with user-defined formula',
      unit: options.unit || '',
    }
  }

  // Run the user-provided formula on the data
  calculate(data) {
    return this.formula(data)
  }

  // Return saved metric information
  getMetadata() {
    return this.metadata
  }
}
