import ChartBase from './ChartBase'
import * as d3 from 'd3'

// D3 bar chart implementation
export default class BarChart extends ChartBase {
  initialize() {
    // Create SVG
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

    // Set dimensions
    this.width =
      this.options.width - this.options.margin.left - this.options.margin.right
    this.height =
      this.options.height - this.options.margin.top - this.options.margin.bottom

    // Setup scales
    this.xScale = d3.scaleBand().range([0, this.width]).padding(0.2)

    this.yScale = d3.scaleLinear().range([this.height, 0])

    // Setup axes
    this.xAxis = d3.axisBottom(this.xScale)
    this.yAxis = d3.axisLeft(this.yScale)

    // Create axes
    this.xAxisElement = this.svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)

    this.yAxisElement = this.svg.append('g').attr('class', 'y-axis')

    // Add labels if provided
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

    this.render()
  }

  render() {
    if (!this.data || this.data.length === 0) return

    // Update domains
    this.xScale.domain(this.data.map(d => d.label))
    this.yScale.domain([0, d3.max(this.data, d => d.value) * 1.1])

    // Update axes
    this.xAxisElement.call(this.xAxis)
    this.yAxisElement.call(this.yAxis)

    // Remove existing bars
    this.svg.selectAll('.bar').remove()

    // Draw bars
    this.svg
      .selectAll('.bar')
      .data(this.data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => this.xScale(d.label))
      .attr('width', this.xScale.bandwidth())
      .attr('y', d => this.yScale(d.value))
      .attr('height', d => this.height - this.yScale(d.value))
      .attr('fill', this.options.barColor || '#4682b4')
      .on('mouseover', function () {
        d3.select(this).attr('fill', '#ff7f0e')
      })
      .on('mouseout', function () {
        d3.select(this).attr('fill', this.options?.barColor || '#4682b4')
      })

    // Add value labels
    if (this.options.showValues) {
      this.svg.selectAll('.bar-label').remove()

      this.svg
        .selectAll('.bar-label')
        .data(this.data)
        .enter()
        .append('text')
        .attr('class', 'bar-label')
        .attr('text-anchor', 'middle')
        .attr('x', d => this.xScale(d.label) + this.xScale.bandwidth() / 2)
        .attr('y', d => this.yScale(d.value) - 5)
        .text(d => d.value)
    }
  }

  destroy() {
    // Clean up
    d3.select(this.container).select('svg').remove()
  }
}
