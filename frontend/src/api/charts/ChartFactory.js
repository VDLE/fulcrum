import LineChart from './LineChart'
import BarChart from './BarChart'
import BubbleChart from './BubbleChart'

// Factory for creating chart instances
export default class ChartFactory {
  // Creates a chart based on type
  static createChart(type, container, data, options = {}) {
    switch (type.toLowerCase()) {
      case 'line':
        return new LineChart(container, data, options)

      case 'bar':
        return new BarChart(container, data, options)

      case 'bubble':
        return new BubbleChart(container, data, options)

      default:
        throw new Error(`Unsupported chart type: ${type}`)
    }
  }
}
