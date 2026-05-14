<template>
  <v-main>
    <v-container class="mt-5 d-flex flex-column align-left">
      <h2 class="mb-6">
        {{ isEditMode ? 'Edit Session Setup' : 'New Session Setup' }}
      </h2>
      <v-row class="d-flex align-start" no-gutters>
        <!-- Trial Config Panel -->
        <v-col cols="12" md="5" class="pr-2">
          <v-card class="pa-4 trial-config-card" elevation="2">
            <h3 class="text-subtitle-1 font-weight-bold mb-2">
              Trial Configuration
            </h3>
            <div class="d-flex align-center gap-4">
              <!-- Trial count field -->
              <v-text-field
                v-model="selectedPermLength"
                label="Trial Count"
                type="number"
                min="1"
                max="100"
                class="flex-grow-1"
                @change="adjustTrialCount"
                :color="isRecLength ? 'warning' : 'primary'"
                :persistent-hint="isRecLength"
                hide-details
              >
              </v-text-field>
              <!-- Randomization btn -->
              <v-btn
                v-tooltip="'Generate Random Permutation'"
                icon
                @click="getPermutation"
                color="transparent"
                class="ml-2"
              >
                <v-icon>mdi-dice-6-outline</v-icon>
              </v-btn>
              <!-- Reset btn -->
              <v-btn
                v-tooltip="'Reset'"
                icon
                @click="resetCount"
                color="transparent"
                class="ml-2"
              >
                <v-icon>mdi-restart</v-icon>
              </v-btn>
            </div>

            <!-- Warning msg for recommended length -->
            <div v-if="isRecLength" class="text-warning text-caption mb-4">
              Recommended {{ recommendedPermLength }} trials for
              {{ recommendationReason }}
            </div>
          </v-card>
        </v-col>
        <!-- Trial coverage heatmap -->
        <v-col cols="12" md="7" class="pl-2">
          <v-card
            class="pa-8 d-flex flex-column justify-center align-center"
            elevation="2"
            style="height: 250px"
          >
            <coverage-heatmap
              v-if="chartReady"
              :tasks="heatmapTasks"
              :factors="heatmapFactors"
              :trials="heatmapMatrix"
              :new-additions="updateNewPairsToHeatmap"
              :chart-height="200"
            />
          </v-card>
        </v-col>
      </v-row>

      <!-- Start of draggable trial cards section -->
      <h3 class="mt-0 mb-2">Pair Tasks & Factors</h3>
      <p
        v-if="study && study.studyDesignType == 'Between'"
        class="mb-2"
        style="color: #2164cf; font-weight: 500"
      >
        Factor selection synced across all trials for "Between" study type
      </p>
      <draggable
        v-model="trials"
        handle=".drag-handle"
        item-key="id"
        animation="200"
        class="w-100"
      >
        <template #item="{ element: trial, index }">
          <v-card
            class="pa-4 mt-2 mb-3 d-flex align-center trial-card"
            elevation="2"
          >
            <div
              class="position-absolute font-weight-bold"
              style="top: 8px; left: 16px; font-size: 16px"
            >
              Trial {{ index + 1 }}
            </div>
            <v-icon class="mr-4 drag-handle" color="grey darken-1"
              >mdi-drag</v-icon
            >
            <v-row>
              <v-col cols="6">
                <!-- Task dropdown -->
                <v-select
                  v-if="study"
                  v-model="trial.taskID"
                  :items="taskOptions"
                  item-title="name"
                  item-value="id"
                  label="Select Task"
                  class="pt-5"
                  :error="!trial.taskID && formValidated"
                ></v-select>
              </v-col>
              <v-col cols="6">
                <!-- Factor dropdown -->
                <v-select
                  v-if="study"
                  v-model="trial.factorID"
                  :items="factorOptions"
                  item-title="name"
                  item-value="id"
                  label="Select Factor"
                  class="pt-5"
                  :error="!trial.factorID && formValidated"
                  @update:modelValue="syncFactorsForBetween($event)"
                ></v-select>
              </v-col>
            </v-row>
            <!-- Delete trial btn -->
            <v-tooltip text="Delete trial">
              <template v-slot:activator="{ props }">
                <v-btn
                  v-if="selectedPermLength > 1"
                  v-bind="props"
                  icon
                  @click="deleteTrial(index)"
                  color="transparent"
                  class="ml-2"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
          </v-card>
        </template>
      </draggable>

      <!-- Add new trial btn-->
      <v-btn
        variant="plain"
        color="grey darken-1"
        class="add-trial-btn"
        @click="addTrial"
        ><strong>+ Add Another Trial</strong></v-btn
      >

      <!-- Save and Cancel btns-->
      <v-row justify="center" class="btn-row">
        <v-btn
          class="me-4 cancel-save-btn"
          color="error"
          @click="
            displayDialog({
              title: 'Cancel Confirmation',
              text: 'Are you sure you want to exit the Session Setup page?',
              source: 'cancel',
            })
          "
          >Cancel</v-btn
        >
        <v-btn
          class="me-4 cancel-save-btn"
          @click="attemptToSave"
          :color="isFormIncomplete ? '#b7ccb2' : 'success'"
          >Save</v-btn
        >
      </v-row>

      <!-- Confirmation Dialog Pop-Up-->
      <div class="text-center pa-4">
        <v-dialog v-model="dialog" max-width="400" persistent>
          <v-card
            prepend-icon="mdi-alert-outline"
            :text="dialogDetails.text"
            :title="dialogDetails.title"
          >
            <template v-slot:actions>
              <v-spacer></v-spacer>

              <v-btn @click="closeDialog()"> Cancel </v-btn>

              <v-btn @click="closeDialog(dialogDetails.source)"> Agree </v-btn>
            </template>
          </v-card>
        </v-dialog>
      </div>
    </v-container>
  </v-main>
</template>

<script>
import api from '@/axiosInstance'
import draggable from 'vuedraggable'
import CoverageHeatmap from '@/components/CoverageHeatmap.vue'
import { useStudyStore } from '@/stores/study'
export default {
  components: {
    draggable,
    CoverageHeatmap,
  },

  data() {
    return {
      chartReady: false,
      studyId: null,
      study: null,
      participantSessionID: null,
      isEditMode: false,
      sessionJson: null,
      // Options that populate the dropdowns
      taskOptions: [],
      factorOptions: [],
      // Stores the currently defined trials
      trials: [],
      // Used for populating dialog pop-ups under diff conditions (ex. cancel vs save)
      dialog: false,
      dialogDetails: {
        title: '',
        text: '',
        source: '',
      },
      // Counts for the number of trials
      selectedPermLength: null,
      recommendedPermLength: null,
      recommendationReason: null, // Coverage or consistency
      formValidated: false,
      // Used for the trial heatmap
      heatmapMatrix: {},
      heatmapTasks: [],
      heatmapFactors: [],
    }
  },

  async mounted() {
    this.studyId = useStudyStore().currentStudyID
    this.participantSessionID = useStudyStore().sessionID
    console.log('Mounted session id:', this.participantSessionID)
    this.isEditMode = !!this.participantSessionID
    await this.getStudyInfo()
    await this.getRecPermLength()
    if (this.isEditMode) {
      await this.fetchSessionSetupJson()
    }
    this.prePopulateTrialCards()
    // Another endpoint call, used to populate the trial coverage heatmap immediately
    this.getTrialOccurrences()
  },

  computed: {
    // Constant check to see if user deviates from recommended perm length
    isRecLength() {
      return this.selectedPermLength != this.recommendedPermLength
    },
    // Form invalid if there is not at least 1 trial or some fields are not filled
    isFormIncomplete() {
      return (
        this.trials.length === 0 ||
        this.trials.some(trial => !trial.taskID || !trial.factorID)
      )
    },
    // Used to update what the heatmap will show as trials are added/removed to the list of draggable trial cards
    updateNewPairsToHeatmap() {
      const definedTrials = []

      for (const trial of this.trials) {
        // Only consider trials that have both a task and factor selected
        if (!trial.taskID || !trial.factorID) {
          continue
        }
        // Get their corresponding names
        const taskName = this.taskOptions.find(t => t.id == trial.taskID)?.name
        const factorName = this.factorOptions.find(
          f => f.id == trial.factorID,
        )?.name
        definedTrials.push({ task: taskName, factor: factorName })
      }
      return definedTrials
    },
  },

  methods: {
    // Dynamic confirmation for canceling or saving session setup details
    displayDialog(details) {
      this.dialogDetails = details
      this.dialog = true
    },

    // If they agree to canceling we route elsewhere & if they click continue we route to demographics form
    async closeDialog(source) {
      const studyStore = useStudyStore()
      studyStore.setDrawerStudyID(this.studyId)
      if (source == 'save') {
        await this.saveSessionJson()
        this.$router.push({
          name: 'UserStudies',
        })
      } else if (source == 'cancel') {
        this.$router.push({
          name: 'UserStudies',
        })
      }
      this.dialog = false
    },

    // Adding a trial
    addTrial() {
      this.trials.push({
        id: Date.now() + Math.random(),
        taskID: null,
        factorID: null,
      })
      this.selectedPermLength = this.trials.length
    },

    // Removes last trial
    removeTrial() {
      this.trials.pop()
      this.selectedPermLength = this.trials.length
    },

    // Deletes a trial at a specific index
    deleteTrial(index) {
      this.trials.splice(index, 1)
      this.selectedPermLength = this.trials.length
    },

    // Updating # of trials present to the recommended # from before
    resetCount() {
      this.selectedPermLength = this.recommendedPermLength
      this.adjustTrialCount()
    },

    // Handles the addition/removal of many trials at once
    adjustTrialCount() {
      const current_length = this.trials.length
      const new_length = Math.min(100, parseInt(this.selectedPermLength) || 1)

      this.selectedPermLength = new_length

      if (new_length < current_length) {
        for (let i = current_length; i > new_length; i--) {
          this.removeTrial()
        }
      } else if (new_length > current_length) {
        for (let i = current_length; i < new_length; i++) {
          this.addTrial()
        }
      }

      this.selectedPermLength = this.trials.length
    },

    // For Between studies, all trials have to have the same factor so if one field changes we update all for consistency
    syncFactorsForBetween(changedFactorID) {
      if (this.study.studyDesignType == 'Between') {
        this.trials = this.trials.map(t => ({
          ...t,
          factorID: changedFactorID,
        }))
      }
    },

    // Retrieves all study details using passed study ID at page mount
    async getStudyInfo() {
      try {
        const response = await api.post('/load_study', {
          studyID: this.studyId,
        })
        this.study = response.data

        console.log(this.study)

        this.taskOptions = this.study.tasks.map(task => ({
          id: task.taskID,
          name: task.taskName,
        }))
        this.factorOptions = this.study.factors.map(factor => ({
          id: factor.factorID,
          name: factor.factorName,
        }))
      } catch (error) {
        console.error('Error fetching study details:', error)
      }
    },

    // Determines what the recommended # of trials should be
    async getRecPermLength() {
      try {
        const path = `/previous_session_length`
        const response = await api.post(path, {
          studyID: this.studyId,
        })

        const prevLength = response.data.prev_length

        if (prevLength == null) {
          // Study has no sessions currently so recommend a length with good coverage
          if (this.study.studyDesignType == 'Within') {
            // Perm of this length would hit all trial combos for Within study type
            this.recommendedPermLength =
              this.taskOptions.length * this.factorOptions.length
          } else {
            // Shorter because we only use 1 factor at a time for Between
            this.recommendedPermLength = this.taskOptions.length
          }
          this.recommendationReason = 'best trial coverage'
        } else {
          // Trial length should be the same as prior sessions for consistency (consider hard enforcing instead of recommending?)
          this.recommendedPermLength = prevLength
          this.recommendationReason = 'consistency with previous sessions'
        }
      } catch (error) {
        console.error('Error fetching study details:', error)
      }
    },

    // Handles trial card population behavior on pg mount depending on new/edit mode
    prePopulateTrialCards() {
      if (this.isEditMode) {
        // Populating trial cards with existing task-factor pairs previously set during initial session setup
        this.trials = this.sessionJson.trials.map(trial => ({
          id: Date.now() + Math.random(),
          taskID: trial.taskID,
          factorID: trial.factorID,
        }))
        this.selectedPermLength = this.trials.length
      } else {
        // Dynamically render empty trial cards based on length recommendation
        for (let i = 0; i < this.recommendedPermLength; i++) {
          this.addTrial()
        }
        this.selectedPermLength = this.recommendedPermLength
      }
    },

    // Grabbing prior session setup json when we are in edit mode
    async fetchSessionSetupJson() {
      try {
        const response = await api.post('/get_session_setup_json', {
          participant_session_id: this.participantSessionID,
        })
        this.sessionJson = response.data
      } catch (err) {
        console.error('Error retrieving existing session setup JSON:', err)
      }
    },

    // Generates a random set of trials for the user that is unique, "random", & balanced
    async getPermutation() {
      try {
        console.log('Selected Perm Length:', this.selectedPermLength)

        const path = `/get_new_trials_perm`
        const response = await api.post(path, {
          study_id: this.studyId,
          trial_count: this.selectedPermLength,
        })

        console.log('Permutations response:', response.data)

        this.trials = response.data.new_perm.map(([taskID, factorID]) => ({
          taskID,
          factorID,
        }))
      } catch (error) {
        console.error('Error fetching random permutation:', error)
      }
    },

    // Retrieves occurences of trials (task-factor combos) in prior sessions (for the trial coverage heatmap)
    async getTrialOccurrences() {
      try {
        const path = `/get_trial_occurrences`
        const response = await api.post(path, {
          study_id: this.studyId,
        })

        this.heatmapTasks = this.taskOptions.map(t => t.name)
        this.heatmapFactors = this.factorOptions.map(f => f.name)
        this.heatmapMatrix = response.data.matrix

        this.$nextTick(() => {
          this.chartReady = true
        })
      } catch (error) {
        console.error('Error fetching trial occurrences:', error)
      }
    },

    // Logic for whether the user clicking "Save" should work or not
    attemptToSave() {
      this.formValidated = true

      if (this.isFormIncomplete) {
        return
      } else {
        this.displayDialog({
          title: 'Save Session Setup',
          text: 'Are you sure you want to save your current session setup?',
          source: 'save',
        })
      }
    },

    // Outputs the session json needed by local scripts to run the session (study json + trial perms + session id = session json)
    createSessionJson() {
      this.sessionJson = {
        participantSessId: this.participantSessionID,
        study_id: this.studyId,
        studyName: this.study.studyName,
        studyDescription: this.study.studyDescription,
        studyDesignType: this.study.studyDesignType,
        participantCount: this.study.participantCount,

        //Add trials array
        trials: this.trials.map(trial => ({
          taskID: trial.taskID,
          factorID: trial.factorID,
          startedAt: null,
        })),

        // Reformat tasks array to dict
        tasks: Object.fromEntries(
          this.study.tasks.map(task => [
            task.taskID.toString(),
            {
              measurementOptions: task.measurementOptions,
              taskDescription: task.taskDescription,
              taskDirections: task.taskDirections,
              taskDuration: task.taskDuration,
              taskName: task.taskName,
            },
          ]),
        ),

        // Reformat the same way for factors
        factors: Object.fromEntries(
          this.study.factors.map(factor => [
            factor.factorID.toString(),
            {
              factorDescription: factor.factorDescription,
              factorName: factor.factorName,
            },
          ]),
        ),
      }

      console.log('Formatted session JSON:', this.sessionJson)
    },

    async saveSessionJson() {
      try {
        if (this.isEditMode) {
          this.createSessionJson() // Formatting the JSON
          await api.post('/overwrite_session_setup_json', {
            participant_session_id: this.participantSessionID,
            session_setup_json: this.sessionJson,
          })
        } else {
          // Reserving the next available participant session id in db ahead of time
          const sessResponse = await api.post(
            '/get_next_participant_session_id',
            { study_id: this.studyId },
          )
          this.participantSessionID = sessResponse.data.participant_session_id
          this.createSessionJson() // Formatting the JSON now that we have the participant session id
          await api.post('/create_participant_session', {
            study_id: this.studyId,
            participant_session_id: this.participantSessionID,
            session_setup_json: this.sessionJson,
          })
        }

        // Clean up session ID after save to avoid issues later
        useStudyStore().clearSessionID()
      } catch (err) {
        console.error('Error saving session setup details', err)
      }
    },
  },
}
</script>

<style scoped>
.trial-card {
  transition: transform 0.25s ease box-shadow 0.25s ease;
}
.trial-card:hover {
  box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
  background-color: #f0f0f0;
}
.drag-handle {
  cursor: grab;
}
.add-trial-btn {
  border-style: dashed !important;
  border-width: 2px !important;
  border-color: #9e9e9e !important;
  color: #616161 !important;
  width: 100%;
  min-height: 50px !important;
  text-transform: none;
}
.btn-row {
  display: flex;
  margin-top: 50px;
}
.cancel-save-btn {
  min-height: 40px;
  min-width: 200px;
}
.trial-config-card {
  height: 175px;
}
</style>
