<template>
  <div class="participant-survey-view">
    <v-tabs v-model="activeTab" background-color="primary" dark>
      <v-tab v-if="surveys.pre" value="pre">Pre-Survey</v-tab>
      <v-tab v-if="surveys.post" value="post">Post-Survey</v-tab>
      <v-tab value="demographic">Demographics</v-tab>
      <v-tab v-if="!surveys.pre && !surveys.post && !demographic" disabled
        >No Data</v-tab
      >
    </v-tabs>

    <!-- Pre/Post Survey Data -->
    <v-card-text
      v-if="
        (activeTab === 'pre' && surveys.pre) ||
        (activeTab === 'post' && surveys.post)
      "
    >
      <v-list>
        <v-list-subheader
          >{{
            activeTab === 'pre' ? 'Pre-Survey' : 'Post-Survey'
          }}
          Responses</v-list-subheader
        >

        <template v-for="(value, key) in activeSurveyData" :key="key">
          <v-divider v-if="!isMetadataField(key)"></v-divider>
          <v-list-item v-if="!isMetadataField(key)">
            <v-list-item-title class="text-subtitle-1 font-weight-medium">
              {{ formatQuestionName(key) }}
            </v-list-item-title>
            <v-list-item-subtitle>
              <div v-if="Array.isArray(value)" class="mt-2">
                <v-chip
                  v-for="(item, i) in value"
                  :key="i"
                  class="ma-1"
                  small
                  >{{ item }}</v-chip
                >
              </div>
              <div v-else>{{ value }}</div>
            </v-list-item-subtitle>
          </v-list-item>
        </template>
      </v-list>
    </v-card-text>

    <!-- Demographic Data -->
    <v-card-text v-else-if="activeTab === 'demographic' && demographic">
      <v-list>
        <v-list-subheader>Demographic Information</v-list-subheader>

        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-title class="text-subtitle-1 font-weight-medium"
            >Age</v-list-item-title
          >
          <v-list-item-subtitle>{{ demographic.age }}</v-list-item-subtitle>
        </v-list-item>

        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-title class="text-subtitle-1 font-weight-medium"
            >Gender</v-list-item-title
          >
          <v-list-item-subtitle>{{ demographic.gender }}</v-list-item-subtitle>
        </v-list-item>

        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-title class="text-subtitle-1 font-weight-medium"
            >Race/Ethnicity</v-list-item-title
          >
          <v-list-item-subtitle>
            <div class="mt-2">
              <v-chip
                v-for="(item, i) in demographic.ethnicity"
                :key="i"
                class="ma-1"
                small
                >{{ item }}</v-chip
              >
            </div>
          </v-list-item-subtitle>
        </v-list-item>

        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-title class="text-subtitle-1 font-weight-medium"
            >Education Level</v-list-item-title
          >
          <v-list-item-subtitle>{{
            demographic.education
          }}</v-list-item-subtitle>
        </v-list-item>

        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-title class="text-subtitle-1 font-weight-medium"
            >Technology Competency</v-list-item-title
          >
          <v-list-item-subtitle
            >{{ demographic.techCompetency }}/10</v-list-item-subtitle
          >
        </v-list-item>
      </v-list>
    </v-card-text>

    <!-- No Data Available -->
    <v-card-text v-else class="text-center pa-6 grey lighten-4">
      <v-icon size="large" color="grey">mdi-clipboard-text-off</v-icon>
      <p class="mt-2">
        {{
          activeTab === 'demographic'
            ? 'No demographic data available for this participant'
            : activeTab
              ? `No ${activeTab}-survey data available for this participant`
              : 'No data available'
        }}
      </p>
    </v-card-text>
  </div>
</template>

<script>
export default {
  name: 'ParticipantSurveyView',
  props: {
    surveys: {
      type: Object,
      default: () => ({ pre: null, post: null }),
    },
    surveyStructure: {
      type: Object,
      default: () => ({ pre: null, post: null }),
    },
    demographic: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      activeTab: 'demographic',
    }
  },
  computed: {
    activeSurveyData() {
      return this.activeTab === 'pre' ? this.surveys.pre : this.surveys.post
    },
  },
  mounted() {
    // Set initial active tab based on available surveys
    if (this.surveys.pre) {
      this.activeTab = 'pre'
    } else if (this.surveys.post) {
      this.activeTab = 'post'
    }
  },
  methods: {
    isMetadataField(key) {
      // Ignore metadata fields from SurveyJS
      const metadataFields = ['pageNo', 'startedAt', 'completedAt']
      return metadataFields.includes(key)
    },
    formatQuestionName(key) {
      // If survey structure is available, get the title from it
      const surveyData =
        this.activeTab === 'pre'
          ? this.surveyStructure.pre
          : this.surveyStructure.post

      if (surveyData && surveyData.elements) {
        // Try to find the question in the survey structure
        const question = surveyData.elements.find(q => q.name === key)
        if (question && question.title) {
          return question.title
        }
      }

      // Fallback: Convert camelCase or snake_case to readable text
      return key
        .replace(/([A-Z])/g, ' $1') // Insert space before capital letters
        .replace(/_/g, ' ') // Replace underscores with spaces
        .toLowerCase()
        .replace(/^\w/, c => c.toUpperCase()) // Capitalize first letter
    },
  },
}
</script>

<style scoped>
.participant-survey-view {
  margin-top: 20px;
}
</style>
