import * as d3 from 'd3'

// renders mouse-specific visuals for learning curve chart
class MouseRenderer {
  // renders aggregated view for mouse metrics
  renderAllTasksView({ chart, data, scales, height }) {
    const { x, y, valueKey = 'mouseDistance' } = scales

    // create orange-to-red gradient for line
    const gradient = chart
      .append('defs')
      .append('linearGradient')
      .attr('id', 'mouse-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '100%')
      .attr('y2', '0%')

    gradient.append('stop').attr('offset', '0%').attr('stop-color', '#FF5722')
    gradient.append('stop').attr('offset', '100%').attr('stop-color', '#FF9800')

    // create smooth curved line
    const line = d3
      .line()
      .x(d => x(d.attempt))
      .y(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX)

    // draw main line with gradient
    chart
      .append('path')
      .datum(data)
      .attr('class', 'line-path')
      .attr('fill', 'none')
      .attr('stroke', 'url(#mouse-gradient)')
      .attr('stroke-width', 4)
      .attr('stroke-linecap', 'round')
      .attr('d', line)

    // add shaded area under curve
    const area = d3
      .area()
      .x(d => x(d.attempt))
      .y0(height)
      .y1(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX)

    chart
      .append('path')
      .datum(data)
      .attr('class', 'area-path')
      .attr('fill', 'url(#mouse-gradient)')
      .attr('fill-opacity', 0.1)
      .attr('d', area)

    // add data point circles
    chart
      .selectAll('.data-point')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'data-point')
      .attr('cx', d => x(d.attempt))
      .attr('cy', d => y(d[valueKey]))
      .attr('r', 7)
      .attr('fill', '#FF9800')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('filter', 'drop-shadow(0px 1px 2px rgba(0,0,0,0.2))')

    // add value labels above points
    chart
      .selectAll('.point-label')
      .data(data)
      .enter()
      .append('text')
      .attr('class', 'point-label')
      .attr('x', d => x(d.attempt))
      .attr('y', d => y(d[valueKey]) - 15)
      .attr('text-anchor', 'middle')
      .text(d => `${Math.round(d[valueKey])}px`)
      .style('font-size', '11px')
      .style('fill', '#333')

    // update chart legend
    const legend = chart.select('.legend')
    legend.selectAll('*').remove()

    legend
      .append('rect')
      .attr('width', 15)
      .attr('height', 15)
      .attr('fill', '#FF9800')

    legend
      .append('text')
      .attr('x', 20)
      .attr('y', 12)
      .text('Mouse Movement')
      .style('font-size', '12px')
  }

  // renders individual task view with separate lines
  renderIndividualTasksView({ chart, data, scales, colorScale, height }) {
    const { x, y, valueKey = 'mouseDistance' } = scales

    // smooth curved line generator
    const line = d3
      .line()
      .x(d => x(d.attempt))
      .y(d => y(d[valueKey]))
      .curve(d3.curveMonotoneX)

    // container for all gradients
    const defs = chart.append('defs')

    // create line for each task with unique color
    data.forEach((task, i) => {
      const color = colorScale(i)

      // create task-specific gradient
      const gradientId = `mouse-gradient-${i}`
      const gradient = defs
        .append('linearGradient')
        .attr('id', gradientId)
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '0%')
        .attr('y2', '100%')

      // gradient from darker to lighter shade
      gradient
        .append('stop')
        .attr('offset', '0%')
        .attr('stop-color', d3.rgb(color).darker(0.3))
      gradient
        .append('stop')
        .attr('offset', '100%')
        .attr('stop-color', color)

      // draw line with gradient
      chart
        .append('path')
        .datum(task.data)
        .attr('class', 'line-path')
        .attr('fill', 'none')
        .attr('stroke', `url(#${gradientId})`)
        .attr('stroke-width', 3)
        .attr('stroke-opacity', 0.8)
        .attr('stroke-linecap', 'round')
        .attr('d', line)

      // add data points
      chart
        .selectAll(`.data-point-${i}`)
        .data(task.data)
        .enter()
        .append('circle')
        .attr('class', 'data-point')
        .attr('cx', d => x(d.attempt))
        .attr('cy', d => y(d[valueKey]))
        .attr('r', 6)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('filter', 'drop-shadow(0px 1px 1px rgba(0,0,0,0.2))')
    })
  }
}

export default MouseRenderer
