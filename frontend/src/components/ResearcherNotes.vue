<template>
  <form @submit.prevent="submit">
    <h2 class="mb-4">Facilitator Notes</h2>
    <!-- Facilitator notice -->
    <v-alert type="info" variant="tonal" prominent class="mb-6">
      <strong> Facilitator Use Only</strong>
    </v-alert>

    <!-- Comments field-->
    <v-textarea
      v-model="comments"
      label="Facilitator Comments"
      counter="250"
      rows="4"
      auto-grow
      :rules="commentsRules"
    />

    <!-- Validate results field-->
    <v-radio-group v-model="isValid">
      <v-label class="mb-2">Validate this session's results?</v-label>
      <v-radio label="Yes" :value="true" />
      <v-radio label="No" :value="false" />
    </v-radio-group>

    <!-- Submit buttton -->
    <v-row class="btn-row" justify="center">
      <v-btn
        class="me-4 submit-btn"
        type="submit"
        :disabled="!isFormValid"
        color="success"
        >Submit</v-btn
      >
    </v-row>
  </form>
</template>

<script>
import api from '@/axiosInstance'
import { useStudyStore } from '@/stores/study'

export default {
  name: 'ResearcherNotes',
  emits: ['submit'],
  props: {
    participantSessId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      comments: '',
      isValid: true,
      saveInProgress: false,
      commentsRules: [
        v => v.length <= 250 || 'Comments must be less than 250 characters.',
      ],
    }
  },

  computed: {
    isFormValid() {
      return this.commentsRules.every(rule => rule(this.comments) === true)
    },
  },

  methods: {
    async submit() {
      if (!this.isFormValid || !this.participantSessId) {
        return
      }
      this.saveInProgress = true
      try {
        const submissionData = {
          participant_session_id: this.participantSessId,
          comments: this.comments,
          is_valid: this.isValid ? 1 : 0,
        }
        const path = `/save_facilitator_session_notes`
        await api.post(path, submissionData)
        this.$emit('submit')
      } catch (error) {
        console.error(
          `Failed to save facilitator notes:`,
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
.submit-btn {
  min-height: 40px;
  min-width: 200px;
}
</style>
