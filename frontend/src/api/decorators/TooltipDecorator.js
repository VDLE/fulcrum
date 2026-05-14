import ChartDecorator from './ChartDecorator'

// Adds tooltips to charts
export default class TooltipDecorator extends ChartDecorator {
  constructor(chart, tooltipOptions = {}) {
    super(chart)
    this.tooltipOptions = {
      formatter: null, // Custom tooltip formatter function
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textColor: '#fff',
      padding: '8px',
      borderRadius: '4px',
      ...tooltipOptions,
    }
  }

  // Override render to add tooltip functionality
  render() {
    // First let the decorated chart render itself
    this.chart.render()

    // Then add tooltip functionality
    this.addTooltips()
  }

  addTooltips() {
    // Implementation depends on chart library being used
    // This is a placeholder implementation
    console.log('Adding tooltips to chart')

    // Get tooltip formatter
    const formatter = this.tooltipOptions.formatter || this.defaultFormatter

    // Apply tooltip configuration
    // This would be implemented differently based on the charting library
    // For example, with D3.js, Chart.js, etc.
  }

  defaultFormatter(data) {
    // Default tooltip formatter - can be overridden
    if (typeof data === 'object') {
      return Object.entries(data)
        .filter(([key]) => !key.startsWith('_'))
        .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
        .join('<br>')
    }
    return data.toString()
  }
}
