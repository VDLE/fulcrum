import * as d3 from 'd3'

/**
 * KeyboardRenderer handles the keyboard-specific rendering for the Task Performance Comparison chart
 */
class KeyboardRenderer {
  /**
   * Render the bar chart with keyboard metrics
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

    // Create key-like bars
    const barGroups = chart
      .selectAll('.bar-group')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'bar-group')

    // Draw key-like shapes
    barGroups.each(function (d, i) {
      const group = d3.select(this)
      const barX = x(d.taskId)
      const barWidth = x.bandwidth()
      const value = metricProcessor.getMetricValue(d, metric)
      const barY = y(value)
      const barHeight = height - barY

      // Add main bar (keyboard key shape)
      group
        .append('rect')
        .attr('class', 'bar')
        .attr('x', barX)
        .attr('width', barWidth)
        .attr('y', height) // Start at bottom for animation
        .attr('height', 0)
        .attr('fill', '#4CAF50')
        .attr('rx', 5) // Rounded corners
        .attr('ry', 5)
        .attr('stroke', '#388E3C')
        .attr('stroke-width', 1.5)
        .transition()
        .duration(800)
        .delay(i * 100)
        .attr('y', barY)
        .attr('height', barHeight)

      // Add key highlight
      group
        .append('rect')
        .attr('class', 'key-highlight')
        .attr('x', barX + 3)
        .attr('width', barWidth - 6)
        .attr('y', height)
        .attr('height', 0)
        .attr('fill', 'rgba(255, 255, 255, 0.3)')
        .attr('rx', 3)
        .attr('ry', 3)
        .transition()
        .duration(800)
        .delay(i * 100)
        .attr('y', barY + 3)
        .attr('height', Math.min(15, barHeight - 6))
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

export default KeyboardRenderer
