import * as d3 from 'd3'

/**
 * PValueRenderer handles the p-value specific rendering for the Task Performance Comparison chart
 */
class PValueRenderer {
  /**
   * Render the bar chart with p-value metric
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
    const baseColor = '#9C27B0' // Purple color for p-value metrics

    // Create gradient definitions for significance levels
    const defs = chart.append('defs')

    // Create different gradients for significance levels
    const highlySignificantGradient = defs
      .append('linearGradient')
      .attr('id', 'highly-significant-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%')

    highlySignificantGradient
      .append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#6A1B9A') // Dark purple

    highlySignificantGradient
      .append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#9C27B0') // Purple

    // Add significance indicators (star icons) at the top of each bar
    const significanceIndicators = chart
      .selectAll('.significance-indicator')
      .data(data)
      .enter()
      .append('g')
      .attr('class', 'significance-indicator')
      .attr('transform', d => {
        const value = metricProcessor.getMetricValue(d, metric)
        const xPos = x(d.taskId) + x.bandwidth() / 2
        const yPos = y(value) - 25 // Position above the bar
        return `translate(${xPos}, ${yPos})`
      })

    // Get different colors for significance levels
    const getBarColor = value => {
      if (value < 0.01) return 'url(#highly-significant-gradient)' // Highly significant
      if (value < 0.05) return '#AB47BC' // Significant
      if (value < 0.1) return '#CE93D8' // Marginally significant
      return '#E1BEE7' // Not significant
    }

    // Get different text colors for significance levels
    const getTextColor = value => {
      if (value < 0.05) return '#7B1FA2' // For significant results
      return '#555' // For less significant results
    }

    // Add bars with significance-based coloring
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
      .attr('fill', d => getBarColor(metricProcessor.getMetricValue(d, metric)))
      .attr('rx', 2) // Rounded corners
      .attr('ry', 2)

    // Animate bars growing upward with significance-based delay
    bars
      .transition()
      .duration(800)
      .delay((d, i) => {
        // Make more significant results appear sooner
        const value = metricProcessor.getMetricValue(d, metric)
        const significanceDelay = value < 0.05 ? 0 : 200
        return i * 50 + significanceDelay
      })
      .attr('y', d => {
        const value = metricProcessor.getMetricValue(d, metric)
        return y(value)
      })
      .attr('height', d => {
        const value = metricProcessor.getMetricValue(d, metric)
        return height - y(value)
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
      .style('fill', d =>
        getTextColor(metricProcessor.getMetricValue(d, metric)),
      )
      .style('font-weight', d =>
        metricProcessor.getMetricValue(d, metric) < 0.05 ? 'bold' : 'normal',
      )
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

export default PValueRenderer
