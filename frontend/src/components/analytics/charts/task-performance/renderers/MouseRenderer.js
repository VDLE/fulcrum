import * as d3 from 'd3'

/**
 * MouseRenderer handles the mouse-specific rendering for the Task Performance Comparison chart
 */
class MouseRenderer {
  /**
   * Render the bar chart with mouse movement metrics
   * @param {Object} options - Rendering options
   * @param {d3.Selection} options.chart - The chart selection
   * @param {Array} options.data - The processed data
   * @param {Object} options.scales - The x and y scales
   * @param {Number} options.height - The chart height
   * @param {Object} options.metricProcessor - The metric processor instance
   * @param {String} options.metric - The current metric
   */
  renderChart({ chart, data, scales, height, metricProcessor, metric }) {
    const { x, y } = scales

    // Create gradient definitions
    const defs = chart.append('defs')

    // Create unique gradient for each bar
    data.forEach((d, i) => {
      const gradientId = `mouseGradient-${d.taskId}`

      const gradient = defs
        .append('linearGradient')
        .attr('id', gradientId)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%')

      gradient.append('stop').attr('offset', '0%').attr('stop-color', '#FF9800')

      gradient
        .append('stop')
        .attr('offset', '100%')
        .attr('stop-color', '#FF5722')
    })

    // Add bars with gradient fill
    const barGroups = chart
      .selectAll('.bar-group')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'bar-group')

    // Add main bar with gradient
    const bars = barGroups
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.taskId))
      .attr('width', x.bandwidth())
      .attr('y', height) // Start at bottom for animation
      .attr('height', 0)
      .attr('fill', d => `url(#mouseGradient-${d.taskId})`)
      .attr('rx', 4) // More rounded corners for mouse metric
      .attr('ry', 4)
      .attr('filter', 'drop-shadow(0px 3px 3px rgba(0,0,0,0.2))')

    // Animate bars growing upward
    bars
      .transition()
      .duration(800)
      .delay((d, i) => i * 100) // Stagger animation
      .attr('y', d => {
        const value = metricProcessor.getMetricValue(d, metric)
        return y(value)
      })
      .attr('height', d => {
        const value = metricProcessor.getMetricValue(d, metric)
        return height - y(value)
      })

    // Add movement lines on top of the bars for visual effect
    data.forEach((d, i) => {
      const numLines = 3 + (i % 3) // Varying number of lines
      const barWidth = x.bandwidth()
      const barX = x(d.taskId)
      const value = metricProcessor.getMetricValue(d, metric)
      const barY = y(value)
      const barHeight = height - barY

      for (let j = 0; j < numLines; j++) {
        const lineY = barY + (j + 1) * (barHeight / (numLines + 1))

        chart
          .append('line')
          .attr('class', 'movement-line')
          .attr('x1', barX)
          .attr('x2', barX + barWidth)
          .attr('y1', lineY)
          .attr('y2', lineY)
          .attr('stroke', 'rgba(255, 255, 255, 0.4)')
          .attr('stroke-width', 1.5)
          .attr('stroke-dasharray', '3,2')
          .attr('opacity', 0)
          .transition()
          .duration(500)
          .delay(800 + i * 100 + j * 50)
          .attr('opacity', 1)
      }
    })

    // Add value labels above bars
    chart
      .selectAll('.bar-label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'bar-label')
      .attr('x', d => x(d.taskId) + x.bandwidth() / 2)
      .attr('y', d => y(metricProcessor.getMetricValue(d, metric)) - 5)
      .attr('text-anchor', 'middle')
      .style('font-size', '11px')
      .style('fill', '#333')
      .style('opacity', 0) // Start invisible for animation
      .text(d =>
        metricProcessor.formatValue(
          metricProcessor.getMetricValue(d, metric),
          metric,
        ),
      )
      .transition()
      .duration(800)
      .delay((d, i) => 300 + i * 100) // Appear after bars
      .style('opacity', 1)
  }
}

export default MouseRenderer
