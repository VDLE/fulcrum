<template>
  <v-card>
    <v-card-title class="pb-0">
      Participant Data
      <v-spacer></v-spacer>
      <!-- Search field to filter the table -->
      <v-text-field
        v-model="search"
        append-icon="mdi-magnify"
        label="Search"
        single-line
        hide-details
        dense
        outlined
        class="search-field"
      ></v-text-field>
    </v-card-title>
    <v-card-subtitle class="pt-1 pb-0">
      <div class="d-flex align-center">
        <small class="text-caption grey--text text--darken-1"
          >Select participants to filter analytics data across all charts</small
        >
        <v-tooltip bottom>
          <template v-slot:activator="{ on, attrs }">
            <v-icon x-small color="grey" class="ml-1" v-bind="attrs" v-on="on">
              mdi-information-outline
            </v-icon>
          </template>
          <span>Use checkboxes to select one or more participants</span>
        </v-tooltip>
      </div>
    </v-card-subtitle>
    <v-card-text>
      <!-- Loading state -->
      <div v-if="loading" class="loading-container">
        <v-progress-circular indeterminate color="primary" />
        <p class="mt-2">Loading participant data...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-container">
        <v-alert type="error" dense>{{ error }}</v-alert>
      </div>

      <!-- Empty state -->
      <div v-else-if="!hasData" class="empty-container">
        <v-icon size="48" color="grey lighten-1"
          >mdi-account-group-outline</v-icon
        >
        <p class="mt-2">No participant data available</p>
      </div>

      <!-- Data table display -->
      <div v-else>
        <!-- Selection indicator -->
        <div v-if="selected.length > 0" class="selection-info mb-3">
          <v-chip color="primary" outlined size="small">
            {{ selected.length }} participant{{
              selected.length !== 1 ? 's' : ''
            }}
            selected
          </v-chip>

          <v-btn
            size="small"
            variant="text"
            density="compact"
            color="primary"
            class="ml-2"
            @click="clearSelection"
          >
            Clear selection
          </v-btn>
        </div>

        <v-table density="compact" class="participant-table">
          <thead class="table-header">
            <tr>
              <th class="text-left select-header">
                <v-checkbox
                  v-model="selectAll"
                  @click="toggleSelectAll"
                  hide-details
                  density="compact"
                ></v-checkbox>
              </th>
              <th v-for="header in headers" :key="header.key" class="text-left">
                {{ header.title }}
              </th>
              <th class="text-center" width="60">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in filteredParticipants" :key="item.participantId">
              <td>
                <v-checkbox
                  v-model="selected"
                  :value="item.participantId"
                  hide-details
                  density="compact"
                  @change="onSelectionChange"
                ></v-checkbox>
              </td>
              <td>{{ (page - 1) * itemsPerPage + index + 1 }}</td>
              <td>{{ item.trialCount }}</td>
              <td>{{ formatTime(item.completionTime) }}</td>
              <td>
                <v-chip
                  size="small"
                  :color="getPValueColor(item.pValue)"
                  text-color="white"
                  class="px-2"
                  variant="elevated"
                >
                  {{ formatPValue(item.pValue) }}
                </v-chip>
              </td>
              <td class="text-center">
                <v-btn
                  icon
                  color="primary"
                  size="x-small"
                  @click="showDetails(item, index)"
                  aria-label="View participant details"
                >
                  <v-icon size="small">mdi-eye</v-icon>
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>

        <!-- Simple pagination -->
        <div class="d-flex align-center justify-end pt-3">
          <span class="text-caption mr-3">Rows per page:</span>
          <v-select
            v-model="itemsPerPage"
            :items="[10, 25, 50, 100]"
            density="compact"
            variant="outlined"
            hide-details
            class="pagination-select mr-3"
          ></v-select>

          <span class="text-caption mr-3">
            {{ paginationStart }}-{{ paginationEnd }} of
            {{ participants.length }}
          </span>

          <v-btn
            icon="mdi-chevron-left"
            size="small"
            variant="text"
            :disabled="page === 1"
            @click="page--"
          ></v-btn>
          <v-btn
            icon="mdi-chevron-right"
            size="small"
            variant="text"
            :disabled="page === totalPages"
            @click="page++"
          ></v-btn>
        </div>
      </div>
    </v-card-text>
  </v-card>

  <!-- Participant Details Modal -->
  <ParticipantDetailsModal
    v-model="showModal"
    :participant="selectedParticipant"
  />
</template>

<script>
import ParticipantDetailsModal from './ParticipantDetailsModal.vue'

export default {
  name: 'ParticipantTable',
  components: {
    ParticipantDetailsModal,
  },
  emits: ['selection-change', 'participants-selected'],
  props: {
    studyId: {
      type: [String, Number],
      required: true,
    },
    participants: {
      type: Array,
      required: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    error: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      search: '', // Search query for filtering
      selected: [], // Array of selected participant IDs
      selectAll: false,
      page: 1,
      itemsPerPage: 25,
      showModal: false,
      selectedParticipant: {},
      headers: [
        {
          title: 'Participant #',
          key: 'participantNumber',
          width: '20%',
          align: 'start',
        },
        {
          title: 'Task Count',
          key: 'trialCount',
          width: '15%',
          align: 'start',
        },
        {
          title: 'Avg. Completion Time',
          key: 'completionTime',
          width: '30%',
          align: 'start',
        },
        {
          title: 'Confidence Level (%)',
          key: 'pValue',
          width: '25%',
          align: 'start',
        },
      ],
    }
  },
  computed: {
    // Quick check if we have data to display
    hasData() {
      return this.participants && this.participants.length > 0
    },

    // Filter participants based on search
    filteredParticipants() {
      if (!this.search) {
        return this.paginatedParticipants
      }

      const searchLower = this.search.toLowerCase()
      const filtered = this.participants.filter(p => {
        return (
          p.participantId.toString().toLowerCase().includes(searchLower) ||
          (p.trialCount &&
            p.trialCount.toString().toLowerCase().includes(searchLower))
        )
      })

      return this.paginate(filtered)
    },

    // Apply pagination to participants
    paginatedParticipants() {
      return this.paginate(this.participants)
    },

    // Calculate total pages
    totalPages() {
      return Math.ceil(this.participants.length / this.itemsPerPage)
    },

    // Calculate pagination display values
    paginationStart() {
      return (this.page - 1) * this.itemsPerPage + 1
    },

    paginationEnd() {
      const end = this.page * this.itemsPerPage
      return end > this.participants.length ? this.participants.length : end
    },
  },
  methods: {
    // Paginate an array
    paginate(items) {
      const start = (this.page - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return items.slice(start, end)
    },

    // Toggle select all participants
    toggleSelectAll() {
      if (this.selectAll) {
        this.selected = this.participants.map(p => p.participantId)
      } else {
        this.selected = []
      }
      this.onSelectionChange()
    },

    // Convert seconds to readable time format with labels
    formatTime(seconds) {
      if (!seconds) return 'N/A'

      // Ensure seconds is a number
      const numSeconds =
        typeof seconds === 'string' ? parseFloat(seconds) : seconds
      if (isNaN(numSeconds)) return 'N/A'

      // Format as seconds if very small
      if (numSeconds < 60) {
        return `${numSeconds.toFixed(1)} sec`
      }

      // Format as minutes and seconds if less than an hour
      if (numSeconds < 3600) {
        const minutes = Math.floor(numSeconds / 60)
        const remainingSeconds = Math.round(numSeconds % 60)
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')} min`
      }

      // Format as hours, minutes, and seconds
      const hours = Math.floor(numSeconds / 3600)
      const minutes = Math.floor((numSeconds % 3600) / 60)
      const remainingSeconds = Math.round(numSeconds % 60)
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')} hrs`
    },

    // Format p-value for display
    formatPValue(pValue) {
      // Check if valid pValue is provided
      if (
        pValue === undefined ||
        pValue === null ||
        isNaN(parseFloat(pValue))
      ) {
        return 'N/A'
      }

      // Ensure pValue is a number
      const numPValue = typeof pValue === 'string' ? parseFloat(pValue) : pValue

      // Convert p-value to confidence percentage
      const confidence = (1 - numPValue) * 100

      // Add stars for significance levels
      let stars = ''
      if (numPValue < 0.01) {
        stars = '★★★' // Highly significant (p < 0.01)
      } else if (numPValue < 0.05) {
        stars = '★★' // Significant (p < 0.05)
      } else if (numPValue < 0.1) {
        stars = '★' // Marginally significant (p < 0.1)
      }

      return confidence.toFixed(1) + '% ' + stars
    },

    // Return color based on p-value significance
    getPValueColor(pValue) {
      // Ensure pValue is a number
      const numPValue = typeof pValue === 'string' ? parseFloat(pValue) : pValue

      if (numPValue < 0.01) return 'purple darken-2' // Very significant
      if (numPValue < 0.05) return 'blue darken-1' // Significant
      if (numPValue < 0.1) return 'amber darken-2' // Marginally significant
      return 'grey darken-1' // Not significant (darker to be more readable)
    },

    // Handle selection change and emit selection event to parent
    onSelectionChange() {
      console.log('ParticipantTable: Selection changed to:', this.selected)

      // Emit the selection change event with selected participant IDs
      this.$emit('selection-change', this.selected)

      // Also emit a formatted selection event with participant data
      const selectedParticipants = this.participants.filter(p =>
        this.selected.includes(p.participantId),
      )

      console.log(
        'ParticipantTable: Emitting selected participant data:',
        selectedParticipants.map(p => ({
          id: p.participantId,
          time: p.completionTime,
        })),
      )

      this.$emit('participants-selected', selectedParticipants)

      // Update selectAll state based on current selection
      this.selectAll = this.selected.length === this.participants.length
    },

    // Clear all selected participants
    clearSelection() {
      this.selected = []
      this.selectAll = false
      this.$emit('selection-change', [])
      this.$emit('participants-selected', [])
    },

    // Show participant details modal
    showDetails(participant, index) {
      // Add studyId and sequential number to the participant object
      const sequentialNumber = (this.page - 1) * this.itemsPerPage + index + 1
      this.selectedParticipant = {
        ...participant,
        studyId: this.studyId,
        sequentialNumber: sequentialNumber
      }
      this.showModal = true
    },
  },
}
</script>

<style scoped>
.search-field {
  max-width: 300px;
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.participant-table {
  width: 100%;
}

.selection-info {
  display: flex;
  align-items: center;
}

.pagination-select {
  width: 80px;
}

/* Custom header styling */
.table-header th {
  font-size: 0.875rem !important;
  font-weight: bold !important;
  color: #37474f !important;
  text-transform: none !important;
  background-color: #f5f5f5 !important;
  padding: 12px 16px !important;
}

.select-header {
  width: 48px !important;
}
</style>
