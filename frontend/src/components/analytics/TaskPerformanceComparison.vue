<template>
  <!-- Forward all props to the modular implementation -->
  <charts-task-performance v-bind="$props" />
</template>

<script>
import ChartsTaskPerformance from './charts/task-performance/TaskPerformanceComparison.vue'

export default {
  name: 'TaskPerformanceComparison',
  // Inherit all the same props from the original component
  props: {
    studyId: {
      type: [Number, String],
      required: true,
    },
    data: {
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
    selectedParticipantIds: {
      type: Array,
      default: () => [],
    },
    participantTaskData: {
      type: Array,
      default: () => [],
    },
    useTestData: {
      type: Boolean,
      default: true, // Default to using test data for development
    },
  },
  components: {
    ChartsTaskPerformance,
  },
}
</script>
