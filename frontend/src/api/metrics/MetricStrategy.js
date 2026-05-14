// Base metric calculation strategy
export default class MetricStrategy {
  constructor() {
    if (this.constructor === MetricStrategy) {
      throw new Error(
        'MetricStrategy is an abstract class and cannot be instantiated directly',
      )
    }
  }

  // Abstract method for calculation
  calculate(data) {
    throw new Error('Method calculate() must be implemented by subclass')
  }

  // Metadata getter
  getMetadata() {
    return {
      name: 'Abstract Metric',
      description: 'Base metric strategy',
      unit: '',
    }
  }
}
