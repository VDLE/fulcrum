<template>
  <v-container fluid>
    <!-- Pre-survey Questions Upload -->
    <FileUploadAndPreview
      :modelValue="preSurveyUpload"
      label="Pre-survey Questionnaire (JSON)"
      accept=".json"
      :preview-disabled="!preSurveyUploadValid"
      @update:modelValue="$emit('update:preSurveyUpload', $event)"
      @preview="showPreSurveyPreview = true"
    ></FileUploadAndPreview>

    <!-- Pre-survey Questions Preview Dialog -->
    <v-dialog v-model="showPreSurveyPreview" class="survey-dialog">
      <v-card title="Pre-survey Questionnaire Preview">
        <v-card-text>
          <Questionnaire :surveyJson="parsedPreSurveyJson" :readOnly="false" />
        </v-card-text>
        <v-card-actions>
          <v-btn text="Close" @click="showPreSurveyPreview = false"></v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Post-survey Questions Upload -->
    <FileUploadAndPreview
      :modelValue="postSurveyUpload"
      label="Post-survey Questionnaire (JSON)"
      accept=".json"
      :preview-disabled="!postSurveyUploadValid"
      @update:modelValue="$emit('update:postSurveyUpload', $event)"
      @preview="showPostSurveyPreview = true"
    ></FileUploadAndPreview>

    <!-- Post-survey Questions Preview Dialog -->
    <v-dialog v-model="showPostSurveyPreview" class="survey-dialog">
      <v-card title="Post-survey Questionnaire Preview">
        <v-card-text>
          <Questionnaire :surveyJson="parsedPostSurveyJson" :readOnly="false" />
        </v-card-text>
        <v-card-actions>
          <v-btn text="Close" @click="showPostSurveyPreview = false"></v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import FileUploadAndPreview from './FileUploadAndPreview.vue'
import Questionnaire from './Questionnaire.vue'
import api from '@/axiosInstance'

export default {
  components: {
    FileUploadAndPreview,
    Questionnaire,
  },
  props: {
    preSurveyUpload: {
      type: [File],
      default: null,
    },
    postSurveyUpload: {
      type: [File],
      default: null,
    },
  },
  emits: [
    'update:preSurveyUpload',
    'update:postSurveyUpload',
    'update:parsedPreSurveyJson',
    'update:parsedPostSurveyJson',
    'update:surveyValidationError',
    'update:surveyValidationErrorMsg',
  ],
  data() {
    return {
      parsedPreSurveyJson: null,
      parsedPostSurveyJson: null,
      preSurveyUploadValid: false,
      postSurveyUploadValid: false,
      showPreSurveyPreview: false,
      showPostSurveyPreview: false,
    }
  },
  watch: {
    // Start validation as soon as survey files are uploaded (pre/post)
    preSurveyUpload: {
      handler(newFile) {
        if (newFile) {
          this.validateSurveyUpload(newFile, 'pre')
        } else {
          this.preSurveyUploadValid = false
          this.parsedPreSurveyJson = null
        }
      },
      immediate: true,
    },
    postSurveyUpload: {
      handler(newFile) {
        if (newFile) {
          this.validateSurveyUpload(newFile, 'post')
        } else {
          this.postSurveyUploadValid = false
          this.parsedPostSurveyJson = null
        }
      },
      immediate: true,
    },
  },
  methods: {
    // Try to validate survey JSON uploads
    async validateSurveyUpload(surveyFile, type) {
      try {
        const fileText = await surveyFile.text()
        const parsedJson = JSON.parse(fileText)

        const path = `validate_survey_upload`
        const response = await api.post(path, parsedJson)

        if (type == 'pre') {
          this.preSurveyUploadValid = true
          this.parsedPreSurveyJson = response.data
          this.$emit('update:parsedPreSurveyJson', response.data)
        } else if (type == 'post') {
          this.postSurveyUploadValid = true
          this.parsedPostSurveyJson = response.data
          this.$emit('update:parsedPostSurveyJson', response.data)
        }
        this.$emit('update:surveyValidationError', false)
        this.$emit('update:surveyValidationErrorMsg', '')
      } catch (err) {
        let error_msg = 'Error occured during survey validation'
        if (err.response?.data?.error_message) {
          const data = err.response.data
          error_msg = data.error_message

          if (data.location?.length) {
            error_msg += ` at ${data.location.join('.')}`
          }
        }
        this.$emit('update:surveyValidationError', true)
        this.$emit('update:surveyValidationErrorMsg', error_msg)

        // Reset values accordingly
        if (type == 'pre') {
          this.preSurveyUploadValid = false
          this.parsedPreSurveyJson = null
        } else if (type == 'post') {
          this.postSurveyUploadValid = false
          this.parsedPostSurveyJson = null
        }
      }
    },
  },
}
</script>

<style scoped>
.survey-dialog {
  width: 60vw;
  max-width: 1500px;
  max-height: none;
}
</style>
