import * as d3 from 'd3'

/**
 * TimeRenderer handles the time-specific rendering for the Task Performance Comparison chart
 */
class TimeRenderer {
  /**
   * Render the bar chart with time metric
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
    const color = '#1976D2' // Blue color for time metrics

    // Add standard bars with animation
    const bars = chart
      .selectAll('.bar')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.taskId))
      .attr('width', x.bandwidth())
      .attr('y', height) // Start at bottom for animation
      .attr('height', 0)
      .attr('fill', color)
      .attr('rx', 2) // Rounded corners
      .attr('ry', 2)

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

    // Add hover effects for bars
    bars
      .on('mouseover', function () {
        d3.select(this).transition().duration(200).attr('opacity', 0.8)
      })
      .on('mouseout', function () {
        d3.select(this).transition().duration(200).attr('opacity', 1)
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

export default TimeRenderer
