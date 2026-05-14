<template>
  <form @submit.prevent="submit">
    <h2>Participant Information</h2>
    <!-- Age field-->
    <v-text-field
      v-model="participantAge"
      type="number"
      label="Age *"
      :rules="participantAgeRules"
    ></v-text-field>
    <!-- Gender field-->
    <v-select
      v-model="participantGender"
      :items="['Male', 'Female', 'Non-Binary', 'Other', 'Prefer Not to Say']"
      label="Gender *"
      :rules="participantGenderRules"
      :menu-props="{ maxHeight: '200px', offsetY: true }"
    ></v-select>
    <!-- Race/Ethnicity field-->
    <v-select
      v-model="participantRaceEthnicity"
      :items="[
        'American Indian or Alaska Native',
        'Asian',
        'Black or African American',
        'Hispanic or Latino',
        'Native Hawaiian or Other Pacific Islander',
        'White',
      ]"
      label="Race/Ethnicity *"
      :rules="participantRaceEthnicityRules"
      multiple
      chips
      :menu-props="{ maxHeight: '200px', offsetY: true }"
    ></v-select>
    <!-- Education lv field -->
    <v-select
      v-model="participantEducationLv"
      :items="[
        'Some High School',
        'High School Graduate or Equivalent',
        'Some College',
        'Associate\'s Degree',
        'Bachelor\'s Degree',
        'Master\'s Degree',
        'Doctorate',
      ]"
      label="Education Level *"
      :rules="participantEducationLvRules"
      :menu-props="{ maxHeight: '200px', offsetY: true }"
    ></v-select>

    <!-- Tech competency field -->
    <v-text-field
      v-model="participantTechCompetency"
      type="number"
      label="Technology Competency (1-10) *"
      :rules="participantTechCompetencyRules"
      :menu-props="{ maxHeight: '200px', offsetY: true }"
    ></v-text-field>

    <!-- Submit button -->
    <v-row class="btn-row" justify="center">
      <v-btn
        class="submit-btn"
        type="submit"
        :disabled="!isFormValid || saveInProgress"
        color="success"
        >Submit</v-btn
      >
    </v-row>
  </form>
</template>

<script>
import api from '@/axiosInstance'

export default {
  name: 'DemographicForm',
  emits: ['submit'],
  props: {
    participantSessId: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      participantAge: '',
      participantGender: '',
      participantRaceEthnicity: [],
      participantEducationLv: '',
      participantTechCompetency: '',
      saveInProgress: false,

      // Form field rules
      participantAgeRules: [
        v => v !== '' || 'Required field.',
        v => Number(v) > 0 || 'Valid inputs must be a number greater than 0.',
        v => Number(v) < 100 || 'Valid inputs must be less than 100.',
      ],
      participantGenderRules: [v => !!v || 'Required field.'],
      participantRaceEthnicityRules: [
        v =>
          (Array.isArray(v) && v.length > 0) ||
          'Must choose at least one option provided.',
      ],
      participantEducationLvRules: [v => !!v || 'Required field.'],
      participantTechCompetencyRules: [
        v => v !== '' || 'Required field.',
        v =>
          (Number(v) >= 1 && Number(v) <= 10) ||
          'Valid inputs must be a number between 1 and 10.',
      ],
    }
  },

  computed: {
    // fxn always checking field inputs and won't allow a session form to be saved
    isFormValid() {
      const ageCheck = this.participantAgeRules.every(
        rule => rule(this.participantAge) === true,
      )
      const genderCheck = this.participantGenderRules.every(
        rule => rule(this.participantGender) === true,
      )
      const raceEthnicityCheck = this.participantRaceEthnicityRules.every(
        rule => rule(this.participantRaceEthnicity) === true,
      )
      const edLvCheck = this.participantEducationLvRules.every(
        rule => rule(this.participantEducationLv) === true,
      )
      const techCompCheck = this.participantTechCompetencyRules.every(
        rule => rule(this.participantTechCompetency) === true,
      )

      return (
        ageCheck &&
        genderCheck &&
        raceEthnicityCheck &&
        edLvCheck &&
        techCompCheck
      )
    },
  },

  methods: {
    async submit() {
      if (!this.isFormValid || this.saveInProgress) {
        return
      }
      this.saveInProgress = true
      try {
        const submissionData = {
          participant_session_id: this.participantSessId,
          participantGender: this.participantGender,
          participantEducationLv: this.participantEducationLv,
          participantAge: this.participantAge,
          participantRaceEthnicity: this.participantRaceEthnicity,
          participantTechCompetency: this.participantTechCompetency,
        }
        const path = `/save_participant_demographics`
        const response = await api.post(path, submissionData)
        this.$emit('submit')
      } catch (error) {
        console.error('Error:', error.response?.data || error.message)
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
