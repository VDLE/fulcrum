<template>
  <div>
    <Questionnaire
      :surveyJson="surveyJson"
      :readOnly="false"
      @submit="saveSurveyResults"
    />
  </div>
</template>

<script>
import Questionnaire from '@/components/Questionnaire.vue'
import api from '@/axiosInstance'

export default {
  name: 'SessionSurvey',
  components: { Questionnaire },
  props: {
    surveyJson: { type: Object, required: true },
    participantSessId: { type: Number, required: true },
    survey_type: { type: String, required: true },
  },
  data() {
    return {
      surveyResultsJson: null,
      surveyComplete: false,
      saveInProgress: false,
    }
  },
  watch: {
    surveyJson: {
      immediate: true,
      handler(newVal) {
        if (newVal && newVal.title) {
          console.log('Survey JSON loaded:', newVal)
        }
      },
    },
  },
  methods: {
    async saveSurveyResults(data) {
      this.surveyResultsJson = data
      this.surveyComplete = true

      if (!this.participantSessId || !this.survey_type) {
        return // Missing fields to save properly
      }

      this.saveInProgress = true // Prevent spam, resulting in multiple saves/endpoint calls
      try {
        const path = `/save_survey_results`
        await api.post(path, {
          participant_session_id: this.participantSessId,
          survey_type: this.survey_type,
          results: this.surveyResultsJson,
        })
        this.$emit('submit')
      } catch (error) {
        console.error(
          `Failed to save ${this.survey_type} survey results:`,
          error.response?.data || error.message,
        )
      } finally {
        this.saveInProgress = false
      }
    },
  },
}
</script>

<style scoped>
.btn-row {
  display: flex;
  margin-top: 50px;
}
.quit-next-btn {
  min-height: 40px;
  min-width: 200px;
}
</style>
