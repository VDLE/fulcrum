import * as d3 from 'd3'
import TimeRenderer from './renderers/TimeRenderer'
import PValueRenderer from './renderers/PValueRenderer'
import MouseRenderer from './renderers/MouseRenderer'
import KeyboardRenderer from './renderers/KeyboardRenderer'
import MetricProcessor from './MetricProcessor'

/**
 * ChartRenderer handles the D3 rendering for the Task Performance Comparison Chart
 */
class ChartRenderer {
  /**
   * Constructor for the chart renderer
   * @param {Object} config - Configuration options for the chart
   */
  constructor(config = {}) {
    this.chart = null
    this.width = 0
    this.height = 0
    this.margin = config.margin || { top: 40, right: 80, bottom: 80, left: 60 }

    // Initialize the metric processor for value formatting
    this.metricProcessor = new MetricProcessor()

    // Initialize the metric-specific renderers
    this.renderers = {
      time: new TimeRenderer(),
      pValue: new PValueRenderer(),
      mouse: new MouseRenderer(),
      keyboard: new KeyboardRenderer(),
    }
  }

  /**
   * Check if the chart has been initialized
   * @returns {Boolean} - True if chart is initialized
   */
  isInitialized() {
    return this.chart !== null
  }

  /**
   * Initialize the chart with the container element
   * @param {HTMLElement} container - The DOM element to contain the chart
   */
  initChart(container) {
    if (!container) return

    // Clear any existing content
    d3.select(container).selectAll('*').remove()

    // Explicitly set dimensions to ensure proper rendering
    const containerHeight = 400
    container.style.height = `${containerHeight}px`

    // Force layout reflow
    void container.offsetHeight

    // Get actual container dimensions after layout
    const containerWidth = Math.max(300, container.clientWidth || 600)

    // Log dimensions for debugging
    console.log(
      `Chart container dimensions: ${containerWidth}×${containerHeight}`,
    )

    // Set dimensions based on container size
    this.width = containerWidth - this.margin.left - this.margin.right
    this.height = containerHeight - this.margin.top - this.margin.bottom

    // Create SVG with responsive viewBox
    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr(
        'viewBox',
        `0 0 ${this.width + this.margin.left + this.margin.right} ${this.height + this.margin.top + this.margin.bottom}`,
      )
      .attr('preserveAspectRatio', 'xMidYMid meet')

    this.chart = svg
      .append('g')
      .attr('transform', `translate(${this.margin.left},${this.margin.top})`)

    // Create axis placeholders
    this.chart
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)

    this.chart.append('g').attr('class', 'y-axis')

    // Add y-axis label
    this.chart
      .append('text')
      .attr('class', 'y-label')
      .attr('text-anchor', 'middle')
      .attr(
        'transform',
        `translate(${-this.margin.left + 15},${this.height / 2}) rotate(-90)`,
      )
      .style('font-size', '12px')
      .style('fill', '#666')
  }

  /**
   * Handle chart resize
   * @param {HTMLElement} container - The DOM element containing the chart
   */
  resize(container) {
    if (!container || !this.chart) return

    // Remove existing chart and reinitialize
    d3.select(container).select('svg').remove()
    this.initChart(container)
  }

  /**
   * Render the bar chart for task comparison
   * @param {Object} options - Rendering options
   * @param {Array} options.data - The processed data
   * @param {String} options.metric - The selected metric
   */
  renderChart({ data, metric }) {
    if (!this.chart || data.length === 0) return

    // Get the appropriate renderer for the metric
    const renderer = this.renderers[metric] || this.renderers.time

    // Set up scales for the bar chart
    const scales = this.createScales(data, metric)

    // Update the y-axis label based on metric
    this.updateYAxisLabel(metric)

    // Update axes
    this.updateAxes(scales, data)

    // Clear existing elements
    this.clearChartElements()

    // Add horizontal grid lines
    this.addGridLines(scales.y)

    // Use the renderer to draw the chart
    renderer.renderChart({
      chart: this.chart,
      data,
      scales,
      height: this.height,
      metricProcessor: this.metricProcessor,
      metric,
    })
  }

  /**
   * Create scales for the bar chart
   * @param {Array} data - The processed data
   * @param {String} metric - The selected metric
   * @returns {Object} - x and y scales
   */
  createScales(data, metric) {
    // Set up x-scale for bar chart (categorical)
    const x = d3
      .scaleBand()
      .domain(data.map(d => d.taskId))
      .range([0, this.width])
      .padding(0.3)

    // Determine y-scale domain based on metric
    let yMin = 0
    let yMax

    switch (metric) {
      case 'time':
        yMax =
          d3.max(data, d => this.metricProcessor.getMetricValue(d, metric)) *
          1.1
        break

      case 'pValue':
        // For p-values, find the actual min and max p-values
        const pValues = data
          .map(d => this.metricProcessor.getMetricValue(d, metric))
          .filter(v => !isNaN(v))
        
        if (pValues.length > 0) {
          // Get the actual max value
          const maxPValue = d3.max(pValues)
          // Add 20% padding for readability
          yMax = Math.min(maxPValue * 1.2, 1.0)
          
          // Ensure yMax is at least 0.05 for visibility, unless all values are smaller
          if (maxPValue < 0.05) {
            yMax = Math.min(0.05, yMax * 3) // Ensure we can see small p-values
          }
        } else {
          // Default to standard 0-1 scale if no data
          yMax = 1.0
        }
        break

      case 'mouse':
      case 'keyboard':
        // For interactive metrics, get max value and add padding
        const values = data
          .map(d => this.metricProcessor.getMetricValue(d, metric))
          .filter(v => !isNaN(v))
        yMax = values.length > 0 ? d3.max(values) * 1.2 : 1000
        break

      default:
        yMax =
          d3.max(data, d => this.metricProcessor.getMetricValue(d, metric)) *
          1.1
    }

    // Create y-scale with padding (capping p-values at 1.0)
    const y = d3
      .scaleLinear()
      .domain([0, metric === 'pValue' ? Math.min(yMax, 1.0) : yMax * 1.2])
      .range([this.height, 0])
      .nice()

    return { x, y }
  }

  /**
   * Update the Y-axis label based on the metric
   * @param {String} metric - The selected metric
   */
  updateYAxisLabel(metric) {
    let yAxisLabel

    switch (metric) {
      case 'time':
        yAxisLabel = 'Avg Time (s)'
        break
      case 'pValue':
        yAxisLabel = 'Raw P-Value'
        break
      case 'mouse':
        yAxisLabel = 'Mouse Movement (pixels)'
        break
      case 'keyboard':
        yAxisLabel = 'Keyboard Actions (count)'
        break
      default:
        yAxisLabel = 'Avg Time (s)'
    }

    this.chart.select('.y-label').text(yAxisLabel)
  }

  /**
   * Update the axes based on the current scales
   * @param {Object} scales - The x and y scales
   * @param {Array} data - The chart data for labels
   */
  updateAxes({ x, y }, data) {
    // Update the x-axis with task names
    const xAxis = this.chart
      .select('.x-axis')
      .transition()
      .duration(500)
      .call(
        d3.axisBottom(x).tickFormat(taskId => {
          const task = data.find(d => d.taskId === taskId)
          if (!task) return ''

          let taskName = task.taskName

          // Remove trailing "task"
          taskName = taskName.replace(/\s+task$/i, '')

          // Remove any double spaces left
          taskName = taskName.replace(/\s{2,}/g, ' ').trim()

          return taskName
        }),
      )

    // Rotate labels to prevent overlap
    xAxis
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-0.5em')
      .attr('dy', '0.15em')
      .attr('transform', 'rotate(-35)')
      .style('font-size', '11px')
      .style('font-weight', '500')

    // Update the y-axis
    this.chart.select('.y-axis').transition().duration(500).call(d3.axisLeft(y))
  }

  /**
   * Add horizontal grid lines to the chart
   * @param {d3.Scale} yScale - The y scale
   */
  addGridLines(yScale) {
    this.chart.selectAll('.grid-line').remove()
    this.chart
      .selectAll('.grid-line-h')
      .data(yScale.ticks(5))
      .enter()
      .append('line')
      .attr('class', 'grid-line')
      .attr('x1', 0)
      .attr('x2', this.width)
      .attr('y1', d => yScale(d))
      .attr('y2', d => yScale(d))
      .attr('stroke', '#e0e0e0')
      .attr('stroke-dasharray', '3,3')
  }

  /**
   * Clear existing chart elements before redrawing
   */
  clearChartElements() {
    this.chart.selectAll('.bar').remove()
    this.chart.selectAll('.bar-label').remove()
    this.chart.selectAll('.key-highlight').remove()
    this.chart.selectAll('.movement-line').remove()
    this.chart.selectAll('defs').remove()
  }
}

export default ChartRenderer
