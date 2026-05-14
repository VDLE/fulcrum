<template>
  <!-- Forward all props to the modular implementation -->
  <charts-learning-curve v-bind="$props" />
</template>

<script>
import ChartsLearningCurve from './charts/learning-curve/LearningCurveChart.vue'

export default {
  name: 'LearningCurveChart',
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
  },
  components: {
    ChartsLearningCurve,
  },
}
</script>
