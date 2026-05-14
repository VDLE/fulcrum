import ChartBase from './ChartBase'
import * as d3 from 'd3'

// Line chart using D3.js
export default class LineChart extends ChartBase {
  initialize() {
    // Create SVG element
    this.svg = d3
      .select(this.container)
      .append('svg')
      .attr('width', this.options.width)
      .attr('height', this.options.height)
      .append('g')
      .attr(
        'transform',
        `translate(${this.options.margin.left},${this.options.margin.top})`,
      )

    // Set chart dimensions
    this.width =
      this.options.width - this.options.margin.left - this.options.margin.right
    this.height =
      this.options.height - this.options.margin.top - this.options.margin.bottom

    // Initialize scales
    this.xScale = d3.scaleLinear().range([0, this.width])

    this.yScale = d3.scaleLinear().range([this.height, 0])

    // Initialize axes
    this.xAxis = d3.axisBottom(this.xScale)
    this.yAxis = d3.axisLeft(this.yScale)

    // Create axes elements
    this.xAxisElement = this.svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)

    this.yAxisElement = this.svg.append('g').attr('class', 'y-axis')

    // Initialize line generator
    this.line = d3
      .line()
      .x(d => this.xScale(d.x))
      .y(d => this.yScale(d.y))

    // Add axis labels if provided
    if (this.options.xAxisLabel) {
      this.svg
        .append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', this.width / 2)
        .attr('y', this.height + this.options.margin.bottom - 5)
        .text(this.options.xAxisLabel)
    }

    if (this.options.yAxisLabel) {
      this.svg
        .append('text')
        .attr('class', 'y-axis-label')
        .attr('text-anchor', 'middle')
        .attr('transform', 'rotate(-90)')
        .attr('x', -this.height / 2)
        .attr('y', -this.options.margin.left + 15)
        .text(this.options.yAxisLabel)
    }

    // Render the chart
    this.render()
  }

  render() {
    if (!this.data || this.data.length === 0) return

    // Update scales domains based on data
    this.xScale.domain([0, d3.max(this.data, d => d.x)])
    this.yScale.domain([0, d3.max(this.data, d => d.y)])

    // Update axes
    this.xAxisElement.call(this.xAxis)
    this.yAxisElement.call(this.yAxis)

    // Remove existing line
    this.svg.selectAll('.line').remove()

    // Add line path
    this.svg
      .append('path')
      .datum(this.data)
      .attr('class', 'line')
      .attr('fill', 'none')
      .attr('stroke', this.options.lineColor || 'steelblue')
      .attr('stroke-width', this.options.lineWidth || 2)
      .attr('d', this.line)

    // Add data points if enabled
    if (this.options.showDataPoints) {
      this.svg.selectAll('.data-point').remove()

      this.svg
        .selectAll('.data-point')
        .data(this.data)
        .enter()
        .append('circle')
        .attr('class', 'data-point')
        .attr('cx', d => this.xScale(d.x))
        .attr('cy', d => this.yScale(d.y))
        .attr('r', this.options.pointRadius || 4)
        .attr('fill', this.options.pointColor || 'steelblue')
    }
  }

  destroy() {
    // Remove the SVG element
    d3.select(this.container).select('svg').remove()
  }
}
