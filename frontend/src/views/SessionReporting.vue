<template>
  <v-main>
    <div class="chart-container">
      <canvas id="scatterChart"></canvas>
    </div>
    <div class="d-flex flex justify-center mt-4">
      <v-btn color="secondary" class="download-btn" @click="getZip">
        <v-icon left>mdi-download</v-icon>
        Download Results
      </v-btn>
    </div>
  </v-main>
</template>

<script>
//
import api from '@/axiosInstance'
import Papa from 'papaparse'
import {
  Chart,
  ScatterController,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Title,
} from 'chart.js'

export default {
  data() {
    return {
      sessionID: null,
    }
  },

  mounted() {
    this.sessionID = this.$route.params.id

    Chart.register(
      ScatterController,
      LinearScale,
      PointElement,
      Tooltip,
      Legend,
      Title,
    )

    const main = async () => {
      //path to files of most recent session
      // const backendPath = `http://127.0.0.1:5001/retrieve_csv/`
      const csvData = [
        '/Task 1_keyboard_data.csv',
        '/Task 1_mouse_clicks_data.csv',
        '/Task 1_mouse_movement_data.csv',
        '/Task 1_mouse_scroll_data.csv',
      ]

      //y-axis labels
      const labels = [
        'Keyboard Inputs',
        'Mouse Movement',
        'Mouse Clicks',
        'Mouse Scrolls',
      ]

      //colors for the different measurement types
      const colors = ['#342d82', '#5f46bc', '#ac81bf', '#d4bfdd']

      //for unique tooltip info based on measurement type
      const tooltipFormats = [
        formatKeyboardData,
        formatMouseData, //for clicks
        formatMouseData, //for movement
        formatMouseData, //for scrolls
      ]

      const datasets = await createDatasets(
        csvData,
        labels,
        colors,
        tooltipFormats,
      )

      const data = { datasets }

      const config = {
        type: 'scatter',
        data: data,
        options: {
          responsive: true,
          maintainAspectRation: true,
          aspectRatio: 2,
          plugins: {
            title: {
              display: true,
              text: 'Task 1 - Factor A', //need to be dynamic eventually
              color: 'black',
              font: {
                size: 32,
                weight: 'bold',
              },
            },
            tooltip: {
              callbacks: {
                label: getTooltip,
              },
            },
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Time (s)',
                color: 'black',
                font: {
                  size: 20,
                  weight: 'bold',
                },
              },
              type: 'linear',
              min: 0,
              position: 'bottom',
            },
            y: {
              display: true,
              title: {
                display: true,
                text: 'Measurement Type',
                color: 'black',
                font: {
                  size: 20,
                  weight: 'bold',
                },
              },
              type: 'linear',
              min: 0,
              max: 5,
              ticks: {
                callback: function (val) {
                  return labels[val - 1] || ''
                },
                stepSize: 1,
                color: 'black',
              },
            },
          },
        },
      }

      //render chart
      const ctx = document.getElementById('scatterChart').getContext('2d')
      new Chart(ctx, config)
    }

    //special tooltip formatting for mouse stuff
    const formatMouseData = measurement => {
      return [
        `Real Time: ${measurement.Time}`,
        `Task Time: ${measurement.running_time}s`,
        `x-coord: ${measurement.x}`,
        `y-coord: ${measurement.y}`,
      ]
    }

    //special tooltip formatting for keyboard stuff
    const formatKeyboardData = measurement => {
      return [
        `Real Time: ${measurement.Time}`,
        `Task Time: ${measurement.running_time}s`,
        `Key Pressed: ${measurement.keys}`,
      ]
    }

    //get unique tooltip labels
    const getTooltip = context => {
      const datasetIndex = context.datasetIndex //index of dataset
      const indexP = context.dataIndex //index of point
      const dataset = context.chart.data.datasets[datasetIndex] //getting actual dataset
      const measurement = dataset.measurements[indexP] //grabbing measurement data now

      return dataset.tooltipFormat(measurement) //formatting the data
    }

    //DOC used: https://www.papaparse.com/docs#local-files
    //purpose is to parse a csv
    const readCSV = file => {
      return new Promise((resolve, reject) => {
        Papa.parse(file, {
          download: true, //URL passed from which we download the file and parse its contents
          header: true, //skip column headers
          skipEmptyLines: true, //if blank lines in csv
          complete: results => resolve(results.data), //receives the parse results when complete
          error: err => reject(err), //if error encountered
        })
      })
    }

    const createDatasets = async (csvData, labels, colors, tooltipFormats) => {
      const datasets = []

      //going through each CSV
      for (let i = 0; i < csvData.length; i++) {
        const data = await readCSV(csvData[i]) //parse current csv w/ fxn above

        const currDataset = {
          //creating array and initializing w/ unique values based on the current iteration/csv
          label: labels[i],
          data: [],
          backgroundColor: colors[i],
          pointRadius: 5,
          measurements: data,
          tooltipFormat: tooltipFormats[i], //keyboard & mouse have diff data points so must account for this
        }

        //going through each row
        for (let j = 0; j < data.length; j++) {
          const tempR = data[j]
          currDataset.data.push({
            x: parseFloat(tempR.running_time), //associated with time relative to task start
            y: i + 1, //height is a set constant here and not indicative of an actual measurement
          })
        }

        datasets.push(currDataset) //adding dataset to datasets array
      }

      return datasets
    }

    main()
  },

  // methods: {
  //   async getZip() {
  //     // get appropriate name based on session id since they are saved as sessionID.zip
  //     const zipName = `${this.sessionID}.zip`
  //     console.log(zipName)
  //     try {
  //       const response = await api.get(
  //         `http://127.0.0.1:5001/retrieve_zip/${zipName}`,
  //         {
  //           responseType: 'blob',
  //         },
  //       )

  //       if (response.data.size === 0) {
  //         return
  //       }
  //       console.log('Received file size:', response.data.size)
  //       const url = window.URL.createObjectURL(new Blob([response.data]))
  //       const link = document.createElement('a')
  //       link.href = url
  //       link.setAttribute('download', zipName)
  //       document.body.appendChild(link)
  //       link.click()
  //       link.remove()
  //     } catch (error) {
  //       console.error('Error downloading ZIP file:', error)
  //     }
  //   },
  // },
}
</script>

<style>
.chart-container {
  width: 70vw;
  height: auto;
  max-height: 70vh;
  aspect-ratio: 2;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
}
.download-btn {
  min-height: 40px;
  max-width: 30px;
  margin-top: 10px;
}
</style>
