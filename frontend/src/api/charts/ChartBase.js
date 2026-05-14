// Abstract base chart class
export default class ChartBase {
  constructor(container, data, options = {}) {
    if (this.constructor === ChartBase) {
      throw new Error(
        'ChartBase is an abstract class and cannot be instantiated directly',
      )
    }

    this.container = container
    this.data = data
    this.options = {
      width: 800,
      height: 400,
      margin: { top: 20, right: 30, bottom: 40, left: 50 },
      ...options,
    }

    this.initialize()
  }

  // Abstract methods
  initialize() {
    throw new Error('Method initialize() must be implemented by subclass')
  }

  render() {
    throw new Error('Method render() must be implemented by subclass')
  }

  // Update data and rerender
  updateData(newData) {
    this.data = newData
    this.render()
  }

  // Update options and rerender
  updateOptions(newOptions) {
    this.options = {
      ...this.options,
      ...newOptions,
    }
    this.render()
  }

  // Cleanup resources
  destroy() {
    // Override in subclasses
  }
}
