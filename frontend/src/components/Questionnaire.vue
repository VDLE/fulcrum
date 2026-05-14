<template>
  <SurveyComponent v-if="survey" :model="survey" />
</template>

<script>
// Referenced Doc for template setup SurveyJS: https://surveyjs.io/form-library/documentation/get-started-vue
import 'survey-core/survey-core.css'
import { Model } from 'survey-core'
import { SurveyComponent } from 'survey-vue3-ui'

export default {
  // eslint-disable-next-line vue/multi-word-component-names
  name: 'Questionnaire',
  components: {
    SurveyComponent,
  },
  props: {
    surveyJson: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      survey: null,
    }
  },
  watch: {
    surveyJson: {
      handler(newJson) {
        if (newJson) {
          const model = new Model(newJson)
          model.readOnly = this.readOnly
          model.onComplete.add(sender => {
            this.$emit('submit', sender.data)
          })
          this.survey = model
        }
      },
      immediate: true,
    },
  },
}
</script>
