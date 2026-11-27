<script setup>
import { ref } from 'vue'

const values = ref('')
const result = ref(null)
const error = ref('')
const pending = ref(false)
const formatNumber = new Intl.NumberFormat(undefined, { maximumSignificantDigits: 8 })
const measures = [
  ['n', 'Count'],
  ['mean', 'Mean'],
  ['median', 'Median'],
  ['mode', 'Mode'],
  ['min', 'Minimum'],
  ['max', 'Maximum'],
  ['range', 'Range'],
  ['variance', 'Sample variance'],
  ['std', 'Sample standard deviation'],
  ['q1', 'First quartile'],
  ['q3', 'Third quartile'],
  ['iqr', 'Interquartile range'],
]

function display(value) {
  if (Array.isArray(value)) {
    return value.length ? value.map((number) => formatNumber.format(number)).join(', ') : 'None'
  }
  return value === null ? 'Unavailable' : formatNumber.format(value)
}

async function calculate() {
  // Clear the previous result so it cannot be mistaken for the current sample.
  result.value = null
  error.value = ''
  pending.value = true
  try {
    const response = await fetch('/api/stats/describe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values: values.value }),
    })
    if (!response.headers.get('content-type')?.includes('application/json')) {
      throw new Error('The stats service is unavailable. Try again.')
    }
    const data = await response.json()
    if (!response.ok) throw new Error(data.error || 'The stats service could not calculate results.')
    result.value = data
  } catch (err) {
    error.value = err.message
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <v-container class="stats-page py-8">
    <h1 class="text-h4 mb-5">Stats Engine</h1>
    <v-card class="pa-5" variant="outlined">
      <form @submit.prevent="calculate">
        <v-textarea
          v-model="values"
          label="Paste numbers"
          hint="Separate numbers with commas, spaces, or new lines."
          maxlength="100000"
          persistent-hint
          :readonly="pending"
          variant="outlined"
          rows="4"
        />
        <v-btn class="mt-4" color="primary" type="submit" :loading="pending">Calculate</v-btn>
      </form>
    </v-card>
    <p v-if="error" class="text-error mt-4" role="alert">{{ error }}</p>
    <section v-if="result" class="mt-6" aria-labelledby="stats-results">
      <h2 id="stats-results" class="text-h6 mb-2">Descriptive statistics</h2>
      <v-table>
        <tbody>
          <tr v-for="[key, label] in measures" :key="key">
            <th scope="row">{{ label }}</th>
            <td>{{ display(result[key]) }}</td>
          </tr>
        </tbody>
      </v-table>
    </section>
  </v-container>
</template>

<style scoped>
.stats-page {
  max-width: 48rem;
}
</style>
