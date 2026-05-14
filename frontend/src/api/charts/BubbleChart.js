import ChartBase from './ChartBase'
import * as d3 from 'd3'

// Bubble chart using D3.js
export default class BubbleChart extends ChartBase {
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

    this.radiusScale = d3.scaleLinear().range([3, 25])

    this.colorScale = d3.scaleOrdinal(d3.schemeCategory10)

    // Initialize axes
    this.xAxis = d3.axisBottom(this.xScale)
    this.yAxis = d3.axisLeft(this.yScale)

    // Create axes elements
    this.xAxisElement = this.svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${this.height})`)

    this.yAxisElement = this.svg.append('g').attr('class', 'y-axis')

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

    // Add tooltip container
    this.tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'd3-tooltip')
      .style('position', 'absolute')
      .style('background-color', 'rgba(0, 0, 0, 0.7)')
      .style('color', 'white')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('pointer-events', 'none')
      .style('opacity', 0)

    // Render the chart
    this.render()
  }

  render() {
    if (!this.data || this.data.length === 0) return

    // Update scales domains based on data
    this.xScale.domain([0, d3.max(this.data, d => d.x) * 1.1])
    this.yScale.domain([0, d3.max(this.data, d => d.y) * 1.1])
    this.radiusScale.domain([0, d3.max(this.data, d => d.r || 1)])

    // Update axes
    this.xAxisElement.call(this.xAxis)
    this.yAxisElement.call(this.yAxis)

    // Remove existing bubbles
    this.svg.selectAll('.bubble').remove()

    const self = this

    // Add bubbles
    this.svg
      .selectAll('.bubble')
      .data(this.data)
      .enter()
      .append('circle')
      .attr('class', 'bubble')
      .attr('cx', d => this.xScale(d.x))
      .attr('cy', d => this.yScale(d.y))
      .attr('r', d => this.radiusScale(d.r || 1))
      .attr('fill', (d, i) =>
        this.options.colorScale
          ? this.options.colorScale(d.category || i)
          : this.colorScale(i),
      )
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('opacity', 0.7)
      .on('mouseover', function (event, d) {
        d3.select(this)
          .attr('stroke', '#000')
          .attr('stroke-width', 2)
          .attr('opacity', 1)

        self.tooltip
          .html(self.formatTooltip(d))
          .style('left', `${event.pageX + 10}px`)
          .style('top', `${event.pageY - 10}px`)
          .style('opacity', 1)
      })
      .on('mouseout', function () {
        d3.select(this)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1)
          .attr('opacity', 0.7)

        self.tooltip.style('opacity', 0)
      })

    // Add labels if enabled
    if (this.options.showLabels) {
      this.svg.selectAll('.bubble-label').remove()

      this.svg
        .selectAll('.bubble-label')
        .data(this.data)
        .enter()
        .append('text')
        .attr('class', 'bubble-label')
        .attr('text-anchor', 'middle')
        .attr('x', d => this.xScale(d.x))
        .attr('y', d => this.yScale(d.y) - this.radiusScale(d.r || 1) - 5)
        .text(d => d.label || '')
    }
  }

  formatTooltip(d) {
    // Default tooltip formatting, can be overridden through options
    if (this.options.tooltipFormatter) {
      return this.options.tooltipFormatter(d)
    }

    let html = ''
    if (d.label) html += `<strong>${d.label}</strong><br>`
    html += `X: ${d.x}<br>Y: ${d.y}`
    if (d.r) html += `<br>Size: ${d.r}`
    if (d.category) html += `<br>Category: ${d.category}`

    return html
  }

  destroy() {
    // Remove the SVG element and tooltip
    d3.select(this.container).select('svg').remove()
    this.tooltip.remove()
  }
}
