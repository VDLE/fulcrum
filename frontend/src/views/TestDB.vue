<template>
  <div>
    <v-btn color="primary" @click="getMessage">{{ msg }}</v-btn>

    <div v-if="result">
      <h3>Response:</h3>
      <p>{{ result }}</p>
    </div>
    <div v-else>
      <p>No response received.</p>
    </div>
  </div>
</template>

<script>
import api from '@/axiosInstance'

export default {
  name: 'TestDatabase',
  data() {
    return {
      msg: 'Fetch Data',
      result: '', // single value from response
    }
  },
  methods: {
    getMessage() {
      const path = `/test_db`
      api
        .get(path)
        .then(res => {
          if (res.data && typeof res.data === 'string') {
            this.result = res.data
            this.msg = 'Data fetched'
          } else {
            this.msg = 'Unexpected response'
          }
        })
        .catch(error => {
          console.error('Error fetching test_db:', error)
          this.msg = 'Error connecting to server'
        })
    },
  },
  mounted() {
    this.getMessage()
  },
}
</script>
