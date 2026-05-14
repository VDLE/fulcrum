<template>
  <v-navigation-drawer
    v-model="drawerProxy"
    location="right"
    temporary
    :width="1250"
  >
    <v-toolbar flat dense color="white">
      <v-toolbar-title> {{ studyName }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn v-tooltip="'Close'" icon @click="closeDrawer">
        <v-icon color="secondary">mdi-close</v-icon>
      </v-btn>
    </v-toolbar>

    <v-divider class="mb-2"></v-divider>

    <v-container class="py-2 px-4">
      <p class="study-description">{{ studyDescription }}</p>
    </v-container>

    <v-container>
      <v-tabs
        v-model="tab"
        background-color="transparent"
        grow
        class="custom-tabs"
      >
        <v-tab>Overview</v-tab>
        <v-tab>Tasks</v-tab>
        <v-tab>Factors</v-tab>
      </v-tabs>

      <v-divider></v-divider>

      <v-card-text>
        <v-tabs-window v-model="tab">
          <!-- Overview Tab -->
          <v-tabs-window-item value="one">
            <v-row>
              <v-col>
                <v-card class="metric-card">
                  <v-icon color="primary">mdi-account-group</v-icon>
                  {{ participantCount + ' expected participants' }}
                </v-card>
                <v-divider class="mb-2"></v-divider>
                <v-card class="metric-card">
                  <v-icon color="primary">mdi-swap-horizontal</v-icon>
                  {{ studyDesignType + ' (study design type)' }}
                </v-card>
                <v-divider class="mb-2"></v-divider>
                <v-card class="metric-card">
                  <v-icon color="primary">mdi-format-list-checks</v-icon>
                  {{ tasks.length + ' tasks' }}
                </v-card>
                <v-divider class="mb-2"></v-divider>
                <v-card class="metric-card">
                  <v-icon color="primary">mdi-vector-combine</v-icon>
                  {{ factors.length + ' factors' }}
                </v-card>
                <v-divider class="mb-2"></v-divider>
              </v-col>
            </v-row>
          </v-tabs-window-item>

          <!-- Tasks Tab -->
          <v-tabs-window-item value="two">
            <h4>Tasks</h4>
            <v-list>
              <v-list-item v-for="(task, index) in tasks" :key="index">
                <v-list-item-title>{{ task.taskName }}</v-list-item-title>
                <v-list-item-subtitle>{{
                  task.taskDescription || 'No task description provided'
                }}</v-list-item-subtitle>
                <p class="task-detail">
                  Duration:
                  {{
                    task.taskDuration && !isNaN(task.taskDuration)
                      ? parseFloat(task.taskDuration).toFixed(2) + ' minutes'
                      : 'No duration set'
                  }}
                </p>
                <p class="task-detail">
                  Measurements Selected:
                  <template v-if="task.measurementOptions.length > 0">
                    <v-chip
                      size="xsmall"
                      variant="tonal"
                      color="primary"
                      rounded
                      v-for="(option, i) in task.measurementOptions"
                      :key="i"
                    >
                      {{ option }}
                    </v-chip>
                  </template>
                  <span v-else>N/A</span>
                </p>
                <v-divider class="mb-2"></v-divider>
              </v-list-item>
            </v-list>
          </v-tabs-window-item>

          <!-- Factors Tab -->
          <v-tabs-window-item value="three">
            <h4>Factors</h4>
            <v-list>
              <v-list-item v-for="(factor, index) in factors" :key="index">
                <v-list-item-title>{{ factor.factorName }}</v-list-item-title>
                <v-list-item-subtitle>{{
                  factor.factorDescription || 'No factor description provided'
                }}</v-list-item-subtitle>
                <v-divider class="mb-2"></v-divider>
              </v-list-item>
            </v-list>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-card-text>
    </v-container>

    <!-- Sessions Tbl -->
    <v-container>
      <v-row class="mb-3">
        <v-col cols="12">
          <h4>Sessions</h4>
          <v-card flat>
            <v-data-table
              :headers="headers"
              :items="sessions"
              dense
              class="elevation-2"
            >
              <template v-slot:item.sessionName="{ item }">
                <div class="study-name">
                  {{ item.sessionName }}
                </div>
              </template>
              <template v-slot:item.status="{ value }">
                <v-chip
                  :color="
                    {
                      complete: 'green',
                      in_progress: 'orange',
                      new: 'blue',
                    }[value]
                  "
                  dark
                >
                  {{
                    value
                      .replace('_', ' ')
                      .replace(/\b\w/g, l => l.toUpperCase())
                  }}
                </v-chip>
              </template>
              <template v-slot:item.validity="{ item }">
                <div v-if="item.status == 'complete'">
                  <v-chip
                    :color="item.validity == 'Valid' ? 'green' : 'red'"
                    dark
                  >
                    {{ item.validity }}
                  </v-chip>
                </div>
                <span v-else class="text-disabled">- -</span>
              </template>
              <template v-slot:item.comments="{ item }">
                <div v-if="item.comments != 'No comments'">
                  {{
                    item.comments.length > 100
                      ? item.comments.substring(0, 100) + '...'
                      : item.comments
                  }}
                </div>
                <span v-else class="text-disabled">- -</span>
              </template>
              <template v-slot:item.actions="{ item }">
                <template v-if="item.status == 'complete'">
                  <v-icon
                    v-tooltip="'Download Results'"
                    class="me-2"
                    size="small"
                    @click.stop="downloadParticipantSessionData(item.sessionID)"
                    >mdi-download</v-icon
                  >
                  <v-icon
                    v-tooltip="'Open'"
                    class="me-2"
                    size="small"
                    @click.stop="openSession(item)"
                    >mdi-arrow-expand</v-icon
                  >
                </template>
                <template v-else-if="item.status == 'new'">
                  <v-icon
                    v-tooltip="'Start Session'"
                    class="me-2"
                    size="small"
                    @click.stop="moveToSessionRunner(item.sessionID)"
                    >mdi-rocket-launch</v-icon
                  >
                  <v-icon
                    v-tooltip="'Edit'"
                    class="me-2"
                    size="small"
                    @click.stop="setupSession(item.sessionID)"
                    >mdi-pencil</v-icon
                  >
                  <v-icon
                    v-tooltip="'Delete'"
                    class="me-2"
                    size="small"
                    @click.stop="deleteSession(item.sessionID)"
                    >mdi-delete</v-icon
                  >
                </template>
                <template v-else-if="item.status == 'in_progress'">
                  <v-icon
                    v-tooltip="'Download Results'"
                    class="me-2"
                    size="small"
                    @click.stop="downloadParticipantSessionData(item.sessionID)"
                    >mdi-download</v-icon
                  >
                  <v-icon
                    v-tooltip="'Resume Session'"
                    class="me-2"
                    size="small"
                    @click.stop="moveToSessionRunner(item.sessionID)"
                    >mdi-play-pause</v-icon
                  >
                </template>
              </template>
            </v-data-table>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
    <v-container class="d-flex flex-column align-center">
      <!-- <h4>Trial Coverage</h4> -->
      <v-card flat style="width: 75%; margin-left: 6%">
        <coverage-heatmap
          :tasks="heatmapTasks"
          :factors="heatmapFactors"
          :trials="heatmapMatrix"
          :chart-height="200"
        />
      </v-card>
    </v-container>

    <v-row justify="center">
      <v-col cols="auto">
        <v-btn @click="setupSession()" color="primary">Setup New Session</v-btn>
      </v-col>
    </v-row>
  </v-navigation-drawer>
</template>

<script>
import api from '@/axiosInstance'
import CoverageHeatmap from '@/components/CoverageHeatmap.vue'
import { useStudyStore } from '@/stores/study'
import { onUnmounted } from 'vue'
export default {
  props: {
    drawer: {
      type: Boolean,
      required: true,
    },
  },
  components: {
    CoverageHeatmap,
  },
  data() {
    return {
      studyName: '',
      studyDescription: '',
      studyDesignType: '',
      participantCount: '',
      tasks: [],
      factors: [],
      tab: null,
      focus_study: '',
      // For the sessions table
      headers: [
        {
          align: 'start',
          key: 'dateCreated',
          sortable: true,
          title: 'Date Created',
        },
        { key: 'sessionName', title: 'Session Name', sortable: false },
        { key: 'status', title: 'Status', sortable: true },
        { key: 'validity', title: 'Validity', sortable: true },
        { key: 'comments', title: 'Comments', sortable: false },
        { key: 'actions', title: 'Actions', sortable: false },
      ],
      sessions: [],

      // Heatmap details
      heatmapMatrix: {},
      heatmapTasks: [],
      heatmapFactors: [],
    }
  },

  computed: {
    drawerProxy: {
      get() {
        // For reading the parent's value (in UserStudies.vue)
        return this.drawer
      },
      set(value) {
        // Emits an update/notification to the parent
        this.$emit('update:drawer', value)
      },
    },
    studyID() {
      return useStudyStore().drawerStudyID
    },
  },

  // Watching for dynamic changes to the studyID and calls fetch route when it changes
  watch: {
    studyID: {
      immediate: true,
      async handler(newID) {
        if (newID) {
          await this.fetchStudyDetails(newID)
          await this.populateSessions(newID)
          await this.getTrialOccurrences()
        } else {
          console.warn('studyID not defined on mount')
        }
      },
    },
  },

  unmounted() {
    const studyStore = useStudyStore()
    studyStore.clearDrawerStudyID()
  },

  methods: {
    // Retrieving all information on the study
    async fetchStudyDetails(studyID) {
      if (!studyID) {
        console.warn('No studyID to use as needed by the route')
        return
      }
      try {
        const response = await api.post('/load_study', { studyID })
        this.focus_study = response.data

        this.studyName = this.focus_study.studyName
        this.studyDescription =
          this.focus_study.studyDescription || 'No study description'
        this.studyDesignType = this.focus_study.studyDesignType
        this.participantCount = this.focus_study.participantCount
        this.tasks = this.focus_study.tasks
        this.factors = this.focus_study.factors
      } catch (error) {
        console.error('Error fetching study details:', error)
      }
    },

    // Download a zip with the data of all sessions under the given study
    async downloadParticipantSessionData(sessionID) {
      try {
        const path = `/get_all_session_data_instance_from_participant_session_zip`

        const response = await api.post(
          path,
          { participant_session_id: sessionID },
          {
            responseType: 'blob',
          },
        )
        // Get the content-disposition header to extract the filename
        const disposition = response.headers['content-disposition']
        const filename = disposition
          ? disposition.split('filename=')[1].replace(/"/g, '') // Extracting the filename from header
          : 'download.zip'

        // Download
        const blob = new Blob([response.data], { type: 'application/zip' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = filename
        link.click()
      } catch (error) {
        console.error('Error downloading session data:', error)
      }
    },

    // Populating the sessions table
    async populateSessions(sessionID) {
      try {
        const path = `/get_all_session_info`
        const response = await api.post(path, { study_id: sessionID })
        console.log('Session found:', response)
        if (Array.isArray(response.data)) {
          this.sessions = response.data.map(session => ({
            sessionID: session[0],
            sessionName: `Session ${session[1]}`,
            dateCreated: session[2],
            status: session[3],
            validity: session[4],
            comments: session[5],
          }))
        }
      } catch (error) {
        console.error('Error retrieving sessions: ', error)
      }
    },

    // Getting trial appearances from prior sessions to populate the heatmap
    async getTrialOccurrences() {
      try {
        const path = `/get_trial_occurrences`
        const response = await api.post(path, { study_id: this.studyID })

        this.heatmapTasks = this.tasks.map(t => t.taskName)
        this.heatmapFactors = this.factors.map(f => f.factorName)
        this.heatmapMatrix = response.data.matrix
      } catch (error) {
        console.error('Error fetching trial occurrences:', error)
      }
    },

    closeDrawer() {
      const studyStore = useStudyStore()
      studyStore.clearDrawerStudyID()
      this.$emit('update:drawer', false)
    },

    // Routes to session reporting pg if user selects a specific session to look at
    openSession(item) {
      const studyStore = useStudyStore()
      studyStore.setSessionID(item.sessionID)
      studyStore.setDrawerStudyID(item.sessionID)
      this.$router.push({
        name: 'DataAnalytics',
      })
    },

    // Route to Session Runner
    moveToSessionRunner(sessionID) {
      const studyStore = useStudyStore()
      studyStore.setSessionID(sessionID)
      studyStore.setDrawerStudyID(this.studyID) // So we can reopen it on return
      this.$router.push({ name: 'SessionRunner' })
    },

    // Route to Session Setup, either creating new or editing existing session
    setupSession(sessionID = null) {
      const studyStore = useStudyStore()
      studyStore.setStudyID(this.studyID) // Needed for SessionSetup
      studyStore.setDrawerStudyID(this.studyID) // So we can reopen it on return

      if (sessionID) {
        studyStore.setSessionID(sessionID) // Edit mode
      } else {
        studyStore.clearSessionID() // New mode
      }

      this.$router.push({ name: 'SessionSetup' })
    },

    // Delete a session (only available for sessions with status "New" for now)
    async deleteSession(sessionID) {
      try {
        const response = await api.post(`/delete_participant_session`, {
          participant_session_id: sessionID,
        })

        if (response.status == 200) {
          this.sessions = this.sessions.filter(s => s.sessionID != sessionID)
        }
      } catch (error) {
        console.error('Error:', error.response?.data || error.message)
      }
    },
  },
}
</script>

<style>
.study-name {
  font-weight: bold;
}
.v-toolbar-title {
  font-size: 18px;
}
.v-divider {
  margin: 10px 0;
}
.elevation-2 {
  background-color: #ffffff;
}
.v-chip {
  font-size: 14px;
  margin: 3px;
  padding: 2px 4px;
}
.custom-tabs {
  background: transparent !important;
  border-bottom: 1px solid #ccc;
}
.v-tab {
  color: #000;
}
.v-tab--active {
  font-weight: bold;
  border-bottom: 2px solid #3f51b5 !important;
  color: #3f51b5 !important;
}
.study-description {
  color: #595959;
  font-size: 14px;
  font-weight: 400;
  margin-bottom: 10px;
}
.task-detail {
  margin-left: 20px;
  font-size: 14px;
  color: #595959;
}
</style>
