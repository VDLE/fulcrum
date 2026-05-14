<template>
  <div class="study-selector">
    <!-- Main study dropdown with search -->
    <v-select
      v-model="selectedStudyId"
      :items="studyOptions"
      item-title="name"
      item-value="id"
      label="Select Study"
      variant="outlined"
      density="compact"
      :loading="loading"
      :error-messages="errorMessage"
      :disabled="disabled || loading || studyOptions.length === 0"
    >
      <!-- Study icon -->
      <template v-slot:prepend>
        <v-icon color="primary">mdi-clipboard-text</v-icon>
      </template>

      <!-- Custom display for selected study -->
      <template v-slot:item="{ item, props }">
        <v-list-item v-bind="props">
          <v-list-item-title>{{ item.raw.name }}</v-list-item-title>
          <v-list-item-subtitle v-if="item.raw.stats">
            {{ item.raw.stats.participants }} participants
          </v-list-item-subtitle>
        </v-list-item>
      </template>

      <!-- Empty state when no studies exist -->
      <template v-slot:no-data>
        <div class="pa-2 text-center">
          <v-icon color="grey-lighten-1" size="24"
            >mdi-alert-circle-outline</v-icon
          >
          <p class="mb-0 mt-1">No studies available</p>
        </div>
      </template>
    </v-select>

    <!-- Refresh button with tooltip -->
    <v-tooltip location="bottom">
      <template v-slot:activator="{ props }">
        <div class="d-inline-block ml-2">
          <v-btn
            icon
            size="small"
            color="primary"
            @click="refreshStudies"
            :loading="loading"
            :disabled="disabled"
            v-bind="props"
          >
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
        </div>
      </template>
      <span>Refresh study list</span>
    </v-tooltip>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analyticsStore'

export default {
  name: 'StudySelector',
  emits: ['study-selected'],

  setup(props, { emit }) {
    const analyticsStore = useAnalyticsStore()
    const loading = ref(false)
    const errorMessage = ref('')
    const disabled = ref(false)
    const selectedStudyId = ref(null)

    // Fetch studies when the component mounts
    onMounted(async () => {
      await fetchStudies()
    })

    // Watch for changes in the selected study
    watch(selectedStudyId, newId => {
      if (newId) {
        emit('study-selected', newId)
      }
    })

    // Computed property to format studies for the dropdown
    const studyOptions = computed(() => {
      console.log(
        'Building study options list with',
        analyticsStore.getStudies.length,
        'studies',
      )
      // Map studies from store to dropdown options
      return analyticsStore.getStudies.map(study => ({
        id: study.id,
        name: study.name,
        description: study.description,
        status: study.status || 'Active',
        stats: study.stats || null,
      }))
    })

    // Method to fetch studies from the API
    const fetchStudies = async () => {
      loading.value = true
      errorMessage.value = ''

      try {
        await analyticsStore.fetchStudies()
        loading.value = false
      } catch (error) {
        console.error('Failed to fetch studies:', error)
        errorMessage.value = 'Failed to load studies'
        loading.value = false
      }
    }

    // Method to refresh studies list
    const refreshStudies = () => {
      fetchStudies()
    }

    return {
      selectedStudyId,
      studyOptions,
      loading,
      errorMessage,
      disabled,
      refreshStudies,
    }
  },
}
</script>

<style scoped>
.study-selector {
  display: flex;
  align-items: center;
  min-width: 250px;
}
</style>
