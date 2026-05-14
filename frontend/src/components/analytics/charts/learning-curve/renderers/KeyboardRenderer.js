import * as d3 from 'd3'

/**
 * KeyboardRenderer handles the keyboard-specific rendering for the Learning Curve Chart
 */
class KeyboardRenderer {
  /**
   * Render the "All Tasks" view with keyboard metrics
   * @param {Object} options - Rendering options
   * @param {d3.Selection} options.chart - The chart selection
   * @param {Array} options.data - The processed data
   * @param {Object} options.scales - The x and y scales
   * @param {Number} options.height - The chart height
   */
  renderAllTasksView({ chart, data, scales, height }) {
    const { x, y, valueKey = 'keyPresses' } = scales
    const color = '#4CAF50' // Green color for keyboard metrics

    // Create a stepped line
    const steppedLine = d3
      .line()
      .x(d => x(d.attempt))
      .y(d => y(d[valueKey]))
      .curve(d3.curveStepAfter) // Stepped line pattern

    // Draw the stepped line
    chart
      .append('path')
      .datum(data)
      .attr('class', 'line-path')
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 3)
      .attr('stroke-dasharray', '1,0') // Solid line
      .attr('d', steppedLine)

    // Add square data points to emphasize discrete nature of keyboard data
    chart
      .selectAll('.data-point')
      .data(data)
      .enter()
      .append('rect')
      .attr('class', 'data-point')
      .attr('x', d => x(d.attempt) - 5)
      .attr('y', d => y(d[valueKey]) - 5)
      .attr('width', 10)
      .attr('height', 10)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('rx', 2) // Slightly rounded corners
      .attr('transform', d => `rotate(45, ${x(d.attempt)}, ${y(d[valueKey])})`) // Diamond shape

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
      .text(d => Math.round(d[valueKey]))
      .style('font-size', '11px')
      .style('fill', '#333')

    // Update the legend
    const legend = chart.select('.legend')
    legend.selectAll('*').remove()

    legend
      .append('rect')
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', color)

    legend
      .append('text')
      .attr('x', 20)
      .attr('y', 12)
      .text('Key Presses')
      .style('font-size', '12px')
  }

  /**
   * Render the "Individual Tasks" view with keyboard metrics
   * @param {Object} options - Rendering options
   * @param {d3.Selection} options.chart - The chart selection
   * @param {Array} options.data - The processed data grouped by task
   * @param {Object} options.scales - The x and y scales
   * @param {d3.Scale} options.colorScale - The color scale for tasks
   * @param {Number} options.height - The chart height
   */
  renderIndividualTasksView({ chart, data, scales, colorScale, height }) {
    const { x, y, valueKey = 'keyPresses' } = scales

    // Draw lines for each task
    data.forEach((task, i) => {
      const color = colorScale(i)

      // Use a stepped line generator
      const steppedLine = d3
        .line()
        .x(d => x(d.attempt))
        .y(d => y(d[valueKey]))
        .curve(d3.curveStepAfter)

      // Add the stepped line
      chart
        .append('path')
        .datum(task.data)
        .attr('class', 'line-path')
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('stroke-dasharray', i % 2 === 0 ? '1,0' : '5,2') // Alternate solid and dashed
        .attr('d', steppedLine)

      // Add square or diamond data points for better distinction
      if (i % 2 === 0) {
        // Even-indexed tasks get squares
        chart
          .selectAll(`.data-point-${i}`)
          .data(task.data)
          .enter()
          .append('rect')
          .attr('class', 'data-point')
          .attr('x', d => x(d.attempt) - 4)
          .attr('y', d => y(d[valueKey]) - 4)
          .attr('width', 8)
          .attr('height', 8)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5)
      } else {
        // Odd-indexed tasks get diamonds
        chart
          .selectAll(`.data-point-${i}`)
          .data(task.data)
          .enter()
          .append('rect')
          .attr('class', 'data-point')
          .attr('x', d => x(d.attempt) - 4)
          .attr('y', d => y(d[valueKey]) - 4)
          .attr('width', 8)
          .attr('height', 8)
          .attr('fill', color)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5)
          .attr(
            'transform',
            d => `rotate(45, ${x(d.attempt)}, ${y(d[valueKey])})`,
          ) // Diamond shape
      }
    })
  }
}

export default KeyboardRenderer
