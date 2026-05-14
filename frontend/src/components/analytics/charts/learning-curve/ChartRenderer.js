import * as d3 from 'd3'
import TimeRenderer from './renderers/TimeRenderer'
import MouseRenderer from './renderers/MouseRenderer'
import KeyboardRenderer from './renderers/KeyboardRenderer'

// handles D3 rendering for learning curve chart
class ChartRenderer {
  constructor(config = {}) {
    this.chart = null
    this.width = 0
    this.height = 0
    this.margin = config.margin || { top: 40, right: 80, bottom: 80, left: 60 }

    // metric-specific renderers
    this.renderers = {
      time: new TimeRenderer(),
      mouse: new MouseRenderer(),
      keyboard: new KeyboardRenderer(),
    }
  }

  // check if chart is ready
  isInitialized() {
    return this.chart !== null
  }

  // create initial chart structure
  initChart(container) {
    if (!container) return

    // clear existing content
    d3.select(container).selectAll('*').remove()

    // calculate dimensions
    this.width = container.clientWidth - this.margin.left - this.margin.right
    this.height = 400 - this.margin.top - this.margin.bottom

    // create responsive SVG container
    const svg = d3
      .select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr(
        'viewBox',
        `0 0 ${this.width + this.margin.left + this.margin.right} ${this.height + this.margin.top + this.margin.bottom + 20}`,
      )
      .attr('preserveAspectRatio', 'xMidYMid meet')

    // create main chart group with margins
    this.chart = svg
      .append('g')
      .attr('transform', `translate(${this.margin.left},${this.margin.top})`)

    // create axes
    this.chart
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)

    this.chart.append('g').attr('class', 'y-axis')

    // add axis labels
    this.chart
      .append('text')
      .attr('class', 'x-label')
      .attr('text-anchor', 'middle')
      .attr('x', this.width / 2)
      .attr('y', this.height + 70)
      .text('Attempt Number')
      .style('font-size', '12px')
      .style('fill', '#666')

    this.chart
      .append('text')
      .attr('class', 'y-label')
      .attr('text-anchor', 'middle')
      .attr(
        'transform',
        `translate(${-this.margin.left + 15},${this.height / 2}) rotate(-90)`,
      )
      .text('Completion Time (s)')
      .style('font-size', '12px')
      .style('fill', '#666')

    // add legend container
    this.chart
      .append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${this.width + 10}, 0)`)
  }

  // handles window resizing
  resize(container) {
    if (!container || !this.chart) return

    // rebuild chart from scratch
    d3.select(container).select('svg').remove()
    this.initChart(container)
  }

  // renders aggregate view of all tasks
  renderAllTasksView({ data, metric }) {
    if (!this.chart || data.length === 0) return

    // update for selected metric
    this.updateYAxisLabel(metric)

    // get appropriate renderer
    const renderer = this.renderers[metric] || this.renderers.time

    // prepare scales & axes
    const scales = this.createScales(data, metric)
    this.updateAxes(scales)

    // clear and prep chart
    this.clearChartElements()
    this.addGridLines(scales.y)

    // render data
    renderer.renderAllTasksView({
      chart: this.chart,
      data,
      scales,
      height: this.height,
    })
  }

  // renders individual view with separate lines for each task
  renderIndividualTasksView({ data, metric }) {
    if (!this.chart || data.length === 0) return

    // update for selected metric
    this.updateYAxisLabel(metric)

    // get appropriate renderer
    const renderer = this.renderers[metric] || this.renderers.time

    // prepare scales & axes
    const scales = this.createScalesForMultipleTasks(data, metric)
    this.updateAxes(scales)

    // clear and prep chart
    this.clearChartElements()
    this.addGridLines(scales.y)

    // create color scheme
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)

    // render data
    renderer.renderIndividualTasksView({
      chart: this.chart,
      data,
      scales,
      colorScale,
      height: this.height,
    })

    // update chart legend
    this.updateLegend(data, metric, colorScale)
  }

  // changes y-axis label based on metric type
  updateYAxisLabel(metric) {
    let yAxisLabel = 'Completion Time (s)'

    if (metric === 'mouse') {
      yAxisLabel = 'Mouse Movement (pixels)'
    } else if (metric === 'keyboard') {
      yAxisLabel = 'Keyboard Actions (count)'
    }

    this.chart.select('.y-label').text(yAxisLabel)
  }

  // creates scales for aggregated view
  createScales(data, metric) {
    // get property name based on metric
    const valueKey = this.getValueKeyForMetric(metric)

    // create x-scale for attempt numbers (starting at 0)
    const x = d3
      .scaleLinear()
      .domain([0, d3.max(data, d => d.attempt)])
      .range([0, this.width])

    // create y-scale for metric values with 10% padding
    const y = d3
      .scaleLinear()
      .domain([0, d3.max(data, d => d[valueKey]) * 1.1])
      .range([this.height, 0])

    return { x, y, valueKey }
  }

  // creates scales for individual tasks view
  createScalesForMultipleTasks(data, metric) {
    // get property name based on metric
    const valueKey = this.getValueKeyForMetric(metric)

    // find max values across all tasks
    const maxAttempt = d3.max(data, d => d3.max(d.data, item => item.attempt))
    const maxValue = d3.max(data, d => d3.max(d.data, item => item[valueKey]))

    // create scales with common domains (x-axis starting at 0)
    const x = d3.scaleLinear().domain([0, maxAttempt]).range([0, this.width])
    const y = d3
      .scaleLinear()
      .domain([0, maxValue * 1.1])
      .range([this.height, 0])

    return { x, y, valueKey }
  }

  // maps metric types to data property names
  getValueKeyForMetric(metric) {
    switch (metric) {
      case 'mouse':
        return 'mouseDistance'
      case 'keyboard':
        return 'keyPresses'
      default:
        return 'completionTime'
    }
  }

  // updates chart axes with animation
  updateAxes({ x, y }) {
    // update x-axis with integer ticks
    this.chart
      .select('.x-axis')
      .transition()
      .duration(500)
      .call(
        d3
          .axisBottom(x)
          .ticks(Math.min(10, d3.max(x.domain())))
          .tickFormat(d3.format('d')),
      )

    // rotate x-axis labels for better readability
    this.chart
      .select('.x-axis')
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)')

    // update y-axis
    this.chart.select('.y-axis').transition().duration(500).call(d3.axisLeft(y))
  }

  // adds horizontal grid lines for readability
  addGridLines(yScale) {
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

  // removes all chart elements before redrawing
  clearChartElements() {
    this.chart.selectAll('.line-path').remove()
    this.chart.selectAll('.data-point').remove()
    this.chart.selectAll('.grid-line').remove()
    this.chart.selectAll('.area-path').remove()
    this.chart.selectAll('.point-label').remove()
    this.chart.selectAll('defs').remove()
  }

  // creates or updates chart legend
  updateLegend(data, metric, colorScale) {
    // clear and rebuild legend
    const legend = this.chart.select('.legend')
    legend.selectAll('*').remove()

    // add entry for each task
    data.forEach((task, i) => {
      const legendItem = legend
        .append('g')
        .attr('transform', `translate(0, ${i * 20})`)

      // color box
      legendItem
        .append('rect')
        .attr('width', 12)
        .attr('height', 12)
        .attr('fill', colorScale(i))

      // task name - without prefixes since they're redundant with the toggle
      legendItem
        .append('text')
        .attr('x', 18)
        .attr('y', 10)
        .text(task.taskName)
        .style('font-size', '12px')
    })
  }
}

export default ChartRenderer
