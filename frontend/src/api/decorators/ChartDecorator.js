// Base decorator for adding features to charts
export default class ChartDecorator {
  constructor(chart) {
    this.chart = chart
  }

  // Delegate methods to decorated chart
  initialize() {
    return this.chart.initialize()
  }

  render() {
    return this.chart.render()
  }

  updateData(newData) {
    return this.chart.updateData(newData)
  }

  updateOptions(newOptions) {
    return this.chart.updateOptions(newOptions)
  }

  destroy() {
    return this.chart.destroy()
  }
}
