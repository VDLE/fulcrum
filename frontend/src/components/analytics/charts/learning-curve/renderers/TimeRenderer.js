import * as d3 from 'd3'

/**
 * TimeRenderer handles the time-specific rendering for the Learning Curve Chart
 */
class TimeRenderer {
  /**
   * Render the "All Tasks" view with time metrics
   * @param {Object} options - Rendering options
   * @param {d3.Selection} options.chart - The chart selection
   * @param {Array} options.data - The processed data
   * @param {Object} options.scales - The x and y scales
   * @param {Number} options.height - The chart height
   */
  renderAllTasksView({ chart, data, scales, height }) {
    const { x, y, valueKey = 'completionTime' } = scales

    // Create the line generator
    const line = d3
      .line()
      .x(d => x(d.attempt))
      .y(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX) // Smooth curve

    // Draw the line with smooth curve
    chart
      .append('path')
      .datum(data)
      .attr('class', 'line-path')
      .attr('fill', 'none')
      .attr('stroke', '#1976D2') // Blue color
      .attr('stroke-width', 3)
      .attr('d', line)

    // Add standard data points
    chart
      .selectAll('.data-point')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'data-point')
      .attr('cx', d => x(d.attempt))
      .attr('cy', d => y(d[valueKey]))
      .attr('r', 6)
      .attr('fill', '#1976D2')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    // Add labels on the points
    chart
      .selectAll('.point-label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'point-label')
      .attr('x', d => x(d.attempt))
      .attr('y', d => y(d[valueKey]) - 15)
      .attr('text-anchor', 'middle')
      .text(d => `${Math.round(d[valueKey])}s`)
      .style('font-size', '11px')
      .style('fill', '#333')

    // Update the legend
    const legend = chart.select('.legend')
    legend.selectAll('*').remove()

    legend
      .append('rect')
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', '#1976D2')

    legend
      .append('text')
      .attr('x', 20)
      .attr('y', 12)
      .text('All Tasks')
      .style('font-size', '12px')
  }

  /**
   * Render the "Individual Tasks" view with time metrics
   * @param {Object} options - Rendering options
   * @param {d3.Selection} options.chart - The chart selection
   * @param {Array} options.data - The processed data grouped by task
   * @param {Object} options.scales - The x and y scales
   * @param {d3.Scale} options.colorScale - The color scale for tasks
   * @param {Number} options.height - The chart height
   */
  renderIndividualTasksView({ chart, data, scales, colorScale, height }) {
    const { x, y, valueKey = 'completionTime' } = scales

    // Create the line generator
    const line = d3
      .line()
      .x(d => x(d.attempt))
      .y(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX)

    // Draw lines for each task
    data.forEach((task, i) => {
      const color = colorScale(i)

      // Draw the line
      chart
        .append('path')
        .datum(task.data)
        .attr('class', 'line-path')
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('d', line)

      // Add data points
      chart
        .selectAll(`.data-point-${i}`)
        .data(task.data)
        .enter()
        .append('circle')
        .attr('class', 'data-point')
        .attr('cx', d => x(d.attempt))
        .attr('cy', d => y(d[valueKey]))
        .attr('r', 5)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
    })
  }
}

export default TimeRenderer
