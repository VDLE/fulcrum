<template>
  <div class="heatmap-container">
    <apexchart
      :key="series"
      ref="chart"
      type="heatmap"
      width="100%"
      :height="chartHeight"
      :options="chartOptions"
      :series="series"
    ></apexchart>
  </div>
</template>

<script>
import VueApexCharts from 'vue3-apexcharts'

// Ref Doc: https://github.com/apexcharts/vue3-apexcharts?tab=readme-ov-file
export default {
  name: 'CoverageHeatmap',
  components: {
    apexchart: VueApexCharts,
  },
  props: {
    tasks: {
      type: Array,
      required: true,
    },
    factors: {
      type: Array,
      required: true,
    },
    trials: {
      type: Object,
      required: true,
    },
    // Allows new trials to be added to the heatmap dynamically for display
    newAdditions: {
      type: Array,
      default: () => [],
    },
    // Makes it so the page calling this componenet can specify a height that works
    chartHeight: {
      type: [String, Number],
      default: 200,
    },
  },
  // Adding in the new trial additions and updating occurence counts
  computed: {
    series() {
      return this.tasks.map(task => {
        return {
          name: task,
          data: this.factors.map(factor => {
            const baseCount = this.trials[task]?.[factor] || 0
            const newCount = this.newAdditions.filter(
              pair => pair.task === task && pair.factor === factor,
            ).length
            const yVal = baseCount + newCount

            return {
              x: factor,
              y: yVal,
            }
          }),
        }
      })
    },
  },
  data() {
    return {
      chartOptions: {
        chart: {
          type: 'heatmap',
          // Ref Doc: https://apexcharts.com/docs/options/chart/toolbar/
          toolbar: {
            show: true,
            offsetX: 0,
            offsetY: 0,
            tools: {
              download: true,
              selection: false,
              zoom: false,
              zoomin: false,
              zoomout: false,
              pan: false,
              reset: false,
            },
          },
        },
        legend: {
          show: false,
        },
        dataLabels: {
          enabled: false,
        },
        colors: ['#4CAF50'],
        plotOptions: {
          heatmap: {
            radius: 2,
            shadeIntensity: 0.5,
            useFillColorAsStroke: false,
            colorScale: {
              inverse: false,
              min: 0,
              ranges: [
                {
                  from: 0,
                  to: 0,
                  color: '#e0e0e0',
                },
              ],
            },
          },
        },
        title: {
          text: 'Trial Coverage',
          align: 'center',
        },
        xaxis: {
          title: { text: 'Factors' },
          labels: { show: false },
          tooltip: { enabled: false },
        },
        yaxis: {
          title: { text: 'Tasks' },
          labels: { show: false },
        },
        //Ref doc: https://apexcharts.com/docs/options/tooltip/#custom
        tooltip: {
          custom: function ({
            series,
            seriesIndex: rowIndex,
            dataPointIndex: colIndex,
            w: content,
          }) {
            const taskName = content.globals.seriesNames[rowIndex]
            const factorName = content.globals.labels[colIndex]
            const occurrences = series[rowIndex][colIndex]

            return `${taskName} x ${factorName}: ${occurrences} ${occurrences == 1 ? 'occurrence' : 'occurrences'}`
          },
        },
      },
    }
  },
}
</script>

<style scoped>
.heatmap-container {
  height: 100%;
  width: 90%;
}
</style>
