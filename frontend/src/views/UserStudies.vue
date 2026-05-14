<template>
  <v-main>
    <v-container class="mt-5">
      <v-row>
        <v-col cols="12">
          <h2>Studies</h2>
        </v-col>
      </v-row>

      <v-row justify="space-between" class="mb-4">
        <v-col cols="12" md="8" lg="9">
          <SearchBar v-model="search" />
        </v-col>
        <v-col cols="12" md="4" lg="3" class="d-flex justify-end">
          <v-btn class="create-study" color="primary" @click="openNewStudy">
            + Create New Study
          </v-btn>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <v-card flat>
            <v-data-table
              :headers="headers"
              :items="studies"
              :search="search"
              class="table-background"
            >
              <template v-slot:item.studyName="{ item }">
                <div class="study-name">
                  {{ item.studyName }}
                </div>
              </template>
              <template v-slot:item.studyDesc="{ item }">
                <div>
                  {{
                    item.studyDesc.length > 100
                      ? item.studyDesc.substring(0, 100) + '...'
                      : item.studyDesc
                  }}
                </div>
              </template>
              <template v-slot:item.sessionCount="{ item }">
                <div>
                  {{ item.sessionCount }}
                </div>
              </template>
              <template v-slot:item.progress="{ item }">
                <v-progress-linear
                  :model-value="calculateProgress(item.sessionCount)"
                  height="15"
                  color="primary"
                >
                </v-progress-linear>
              </template>
              <template v-slot:item.actions="{ item }">
                <v-icon
                  v-tooltip="'Download Results'"
                  class="me-2"
                  size="small"
                  @click.stop="downloadStudyData(item.studyID)"
                >
                  mdi-download
                </v-icon>

                <v-icon
                  v-tooltip="'Open'"
                  class="me-2"
                  size="small"
                  @click.stop="openDrawer(item.studyID)"
                >
                  mdi-arrow-expand
                </v-icon>

                <!-- Only Owner and Editor can Share -->
                <v-icon
                  v-if="['Owner', 'Editor', 'Viewer'].includes(item.role)"
                  v-tooltip="'Share'"
                  class="me-2"
                  size="small"
                  @click.stop="openShareDialog(item)"
                >
                  mdi-share-variant
                </v-icon>

                <!-- Only Owner and Editor can Edit -->
                <v-icon
                  v-if="['Owner', 'Editor'].includes(item.role) && item.canEdit"
                  v-tooltip="'Edit'"
                  class="me-2"
                  size="small"
                  @click.stop="editExistingStudy(item.studyID)"
                >
                  mdi-pencil
                </v-icon>

                <v-icon
                  v-tooltip="'Duplicate'"
                  class="me-2"
                  size="small"
                  @click.stop="duplicateStudy(item.studyID)"
                >
                  mdi-content-copy
                </v-icon>

                <!-- Only Owner can Delete -->
                <v-icon
                  v-if="item.role === 'Owner'"
                  v-tooltip="'Delete'"
                  size="small"
                  @click="openDeleteConfirmation(item.studyID)"
                >
                  mdi-delete
                </v-icon>
              </template>
            </v-data-table>
          </v-card>
        </v-col>
      </v-row>

      <StudyPanel
        v-if="drawer && studyStore.drawerStudyID"
        :drawer="drawer"
        @update:drawer="handleDrawerUpdate"
        @close="drawer = false"
      />
      <v-dialog v-model="shareDialog" persistent width="640">
        <v-slide-y-transition mode="in-out">
          <v-card v-if="shareDialog" elevation="4" class="pa-6 share-card">
            <!-- Top Bar -->
            <v-card-title class="d-flex justify-space-between align-center">
              <span class="share-title">Share "{{ sharingStudyName }}"</span>
            </v-card-title>
            <v-card-text>
              <!-- Only show add user form if user has permission -->
              <div
                class="d-flex align-center mb-4"
                v-if="['Owner', 'Editor'].includes(requestingUserRole)"
              >
                <v-text-field
                  v-model="newShareEmail"
                  label="Add people, groups, or emails"
                  prepend-inner-icon="mdi-account-plus"
                  class="flex-grow-1 mr-4"
                  density="comfortable"
                  hide-details="auto"
                  outlined
                  @keyup.enter="handleEnter"
                />

                <v-select
                  v-if="showRoleSelector"
                  v-model="newUserRole"
                  :items="['Viewer', 'Editor']"
                  label="Role"
                  hide-details
                  dense
                  outlined
                  style="width: 130px"
                  @change="confirmAddUser"
                />
              </div>

              <!-- People With Access Label -->
              <p class="people-access-label mb-2">People with access</p>

              <!-- User Rows -->
              <v-list class="pa-0" elevation="0">
                <div
                  v-for="(user, index) in sortedUsers"
                  :key="index"
                  class="d-flex align-center justify-space-between user-row px-2 py-2"
                >
                  <!-- Avatar -->
                  <v-avatar size="36" class="mr-4">
                    <img src="/images/unr n.jpg" alt="pfp" />
                  </v-avatar>

                  <!-- Email + Role (flex grow) -->
                  <div
                    class="d-flex align-center flex-grow-1 justify-space-between"
                  >
                    <!-- Email -->
                    <span class="user-email">{{ user.email }}</span>

                    <!-- Role -->
                    <v-select
                      v-if="canChangeRole(user)"
                      v-model="user.role"
                      :items="['Viewer', 'Editor']"
                      dense
                      hide-details
                      class="role-select"
                      @update:modelValue="val => changeUserAccess(user, val)"
                    />

                    <span v-else class="user-role ml-4">
                      {{ user.role }}
                    </span>
                  </div>

                  <!-- Trash icon for Owners removing others -->
                  <v-btn
                    v-if="
                      requestingUserRole === 'Owner' &&
                      user.role !== 'Owner' &&
                      user.email !== currentUserEmail
                    "
                    icon
                    @click="removeSharedUser(user.email)"
                    class="ml-2"
                    color="transparent"
                  >
                    <v-icon>mdi-trash-can-outline</v-icon>
                  </v-btn>
                </div>
              </v-list>
              <v-alert
                v-if="errorMessage"
                type="error"
                class="mt-4 text-center"
                variant="outlined"
              >
                {{ errorMessage }}
              </v-alert>

              <v-alert
                v-if="successMessage"
                type="success"
                class="mt-4 text-center"
                variant="outlined"
              >
                {{ successMessage }}
              </v-alert>

              <!-- Done and Leave Buttons -->
              <v-row justify="end" class="mt-4" align="center" no-gutters>
                <v-btn
                  v-if="
                    requestingUserRole === 'Editor' ||
                    requestingUserRole === 'Viewer'
                  "
                  color="error"
                  class="mr-4"
                  @click="openLeaveConfirmation"
                >
                  <v-icon left>mdi-exit-run</v-icon> Leave Study
                </v-btn>

                <v-btn color="primary" @click="shareDialog = false">
                  Done
                </v-btn>
              </v-row>
            </v-card-text>
          </v-card>
        </v-slide-y-transition>
      </v-dialog>
      <ConfirmationDialog
        v-model="confirmLeaveDialog"
        :dialogDetails="leaveDialogDetails"
        @confirm="performLeaveStudy"
        @cancel="confirmLeaveDialog = false"
      />
    </v-container>
  </v-main>
</template>

<script>
import StudyPanel from '@/components/StudyPanel.vue'
import SearchBar from '@/components/SearchBar.vue'
import ConfirmationDialog from '@/components/ConfirmationDialog.vue'
import api from '@/axiosInstance'
import { useStudyStore } from '@/stores/study'
export default {
  components: { StudyPanel, SearchBar, ConfirmationDialog },
  setup() {
    const studyStore = useStudyStore()
    return { studyStore }
  },
  data() {
    return {
      confirmLeaveDialog: false,
      leaveDialogDetails: {
        title: '',
        text: '',
        source: '',
      },
      errorMessage: '',
      successMessage: '',
      showRoleSelector: false,
      currentUserEmail: '',
      shareDialog: false,
      newShareEmail: '',
      newUserRole: '',
      currentStudyForSharing: null,
      sharedUsers: [],
      sharingStudyName: '',
      search: '',
      drawer: false,
      selectedStudy: {},
      headers: [
        {
          align: 'start',
          key: 'dateCreated',
          sortable: false,
          title: 'Date Created',
        },
        {
          key: 'studyName',
          title: 'User Study Name',
          sortable: false,
          width: '250px',
        },
        { key: 'studyDesc', title: 'Description', sortable: false },
        { key: 'sessionCount', title: 'Sessions', sortable: false },
        { key: 'progress', title: 'Progress', sortable: false, width: '200px' },
        { key: 'role', title: 'Role', sortable: false },
        { key: 'actions', title: 'Actions', sortable: false },
      ],
      studies: [],
    }
  },
  computed: {
    sortedUsers() {
      const currentUser = this.sharedUsers.find(
        u => u.email === this.currentUserEmail,
      )
      const others = this.sharedUsers.filter(
        u => u.email !== this.currentUserEmail,
      )
      return currentUser ? [currentUser, ...others] : this.sharedUsers
    },
  },
  async mounted() {
    const studyStore = useStudyStore()
    studyStore.clearSessionID()
    await this.populateStudies()

    if (studyStore.drawerStudyID) {
      this.openDrawer(studyStore.drawerStudyID)
    }
  },
  confirmLeaveStudy() {
    this.displayDialog({
      title: 'Leave Study?',
      text: 'Are you sure you want to leave this study?',
      action: 'leave', // custom field to distinguish
    })
  },

  methods: {
    handleDrawerUpdate(newVal) {
      this.drawer = newVal
      if (!newVal) {
        const studyStore = useStudyStore()
        studyStore.clearDrawerStudyID()
      }
    },
    openLeaveConfirmation() {
      this.leaveDialogDetails = {
        title: 'Leave Study?',
        text: 'You will lose access to this study. Are you sure you want to leave?',
        source: 'leave',
      }
      this.confirmLeaveDialog = true
    },
    openDeleteConfirmation(studyID) {
      this.leaveDialogDetails = {
        title: 'Delete Study?',
        text: 'Are you sure you want to delete this study?',
        source: 'delete',
        studyID: studyID,
      }
      this.confirmLeaveDialog = true
    },

    async performLeaveStudy() {
      try {
        if (this.leaveDialogDetails.source === 'leave') {
          const res = await api.post('/leave_user_study_access', {
            studyID: this.currentStudyForSharing.studyID,
            desiredUserEmail: this.currentUserEmail,
          })

          if (res.status === 200) {
            this.successMessage = 'You have left the study.'
            this.shareDialog = false
            await this.populateStudies()
          } else {
            this.errorMessage = 'Failed to leave the study.'
          }
        } else if (this.leaveDialogDetails.source === 'delete') {
          const res = await api.post('/delete_study', {
            studyID: this.leaveDialogDetails.studyID,
          })

          if (res.status === 200) {
            this.successMessage = 'Study deleted successfully.'
            await this.populateStudies()
          } else {
            this.errorMessage = 'Failed to delete study.'
          }
        }
      } catch (error) {
        console.error('Error performing action:', error)
        this.errorMessage = 'Error trying to perform the action.'
      }
    },
    async removeMyselfFromStudy() {
      if (!this.currentStudyForSharing) return

      try {
        const res = await api.post('/leave_user_study_access', {
          studyID: this.currentStudyForSharing.studyID,
          desiredUserEmail: this.currentUserEmail,
        })

        if (res.status === 200) {
          this.successMessage = 'You have left the study.'
          this.shareDialog = false
          await this.populateStudies() // Refresh the studies list
        } else {
          this.errorMessage = 'Failed to leave the study.'
        }
      } catch (err) {
        console.error('Error leaving study:', err)
        this.errorMessage = 'Error trying to leave the study.'
      }
    },
    canChangeRole(user) {
      if (this.requestingUserRole === 'Owner') {
        return user.role !== 'Owner'
      }

      if (this.requestingUserRole === 'Editor') {
        return user.role === 'Viewer'
      }

      return false
    },
    async handleEnter() {
      this.errorMessage = ''
      this.successMessage = ''
      if (!['Owner', 'Editor'].includes(this.requestingUserRole)) {
        this.errorMessage = "You don't have permission to add users."
        return
      }

      if (!this.currentStudyForSharing) {
        this.errorMessage = 'No study selected to share.'
        return
      }

      try {
        const res = await api.post('/check_user_exists', {
          desiredUserEmail: this.newShareEmail,
        })
        if (res.data.exists == 'false') {
          this.errorMessage = 'User does not exist.'
          return
        }

        this.newUserRole = 'Viewer'
        await this.confirmAddUser()
      } catch (err) {
        console.error('Error checking user:', err)

        const data = err?.response?.data
        const msg =
          typeof data === 'object'
            ? data.message || data.error || 'Something went wrong.'
            : 'Something went wrong.'

        this.errorMessage = msg
      }
    },
    // Called when role is selected
    async confirmAddUser() {
      this.successMessage = ''
      this.errorMessage = ''

      if (!this.newShareEmail || !this.newUserRole) return

      try {
        const res = await api.post('/add_user_study_access', {
          studyID: this.currentStudyForSharing.studyID,
          desiredUserEmail: this.newShareEmail,
          roleType: this.newUserRole,
        })

        if (res.status === 200) {
          this.successMessage = 'User added successfully.'
          this.newShareEmail = ''
          this.newUserRole = ''
          this.showRoleSelector = false
          this.openShareDialog(this.currentStudyForSharing) // Refresh
        } else {
          // Catch unexpected non-200 responses
          const msg =
            res.data?.message || res.data?.error || typeof res.data === 'string'
              ? res.data
              : 'Failed to add user.'
          this.errorMessage = msg
        }
      } catch (err) {
        const data = err?.response?.data
        const msg =
          data?.message ||
          data?.error ||
          (typeof data === 'string' ? data : 'Error adding user.')
        this.errorMessage = msg
      }
    },
    async openShareDialog(study) {
      this.successMessage = ''
      this.errorMessage = ''

      this.currentStudyForSharing = study
      this.shareDialog = true
      this.sharedUsers = []
      this.requestingUserRole = study.role

      try {
        const res = await api.post('/get_all_user_access_for_study', {
          studyID: study.studyID,
        })

        if (res.status === 200) {
          this.sharedUsers = res.data.data.map(user => ({
            email: user[0],
            role: user[1],
          }))
          this.requestingUserRole = res.data["requesting user's role"]
          this.currentUserEmail = res.data["requesting user's email"]
          this.sharingStudyName = res.data.study_name
        }
      } catch (error) {
        console.error('Error fetching sharing data:', error)
        this.errorMessage = 'Could not fetch sharing info.'
      }
    },
    async removeSharedUser(userEmail) {
      this.successMessage = ''
      this.errorMessage = ''

      if (this.requestingUserRole !== 'Owner') {
        this.errorMessage = 'Only owners can remove users.'
        return
      }

      try {
        const res = await api.post('/remove_user_study_access', {
          studyID: this.currentStudyForSharing.studyID,
          desiredUserEmail: userEmail,
        })

        if (res.status === 200) {
          this.successMessage = 'User removed.'
          this.openShareDialog(this.currentStudyForSharing)
        } else {
          this.errorMessage = 'Failed to remove user.'
        }
      } catch (err) {
        this.errorMessage = 'Error removing user.'
      }
    },
    async changeUserAccess(user, newRole) {
      this.successMessage = ''
      this.errorMessage = ''

      console.log('Changing:', user.email)

      try {
        const res = await api.post('/change_user_access_type', {
          studyID: this.currentStudyForSharing.studyID,
          desiredUserEmail: user.email,
          roleType: newRole,
        })

        if (res.status === 200) {
          this.successMessage = 'Role updated.'
          this.openShareDialog(this.currentStudyForSharing)
        } else {
          this.errorMessage = 'Failed to update role.'
        }
      } catch (err) {
        const msg = err?.response?.data?.message || 'Error updating role.'
        this.errorMessage = msg
      }
    },
    async populateStudies() {
      try {
        const response = await api.get('/get_study_data')

        if (Array.isArray(response.data)) {
          this.studies = await Promise.all(
            response.data.map(async study => {
              const canEdit = await this.checkIfOverwriteAllowed(study[1])
              return {
                dateCreated: study[0],
                studyID: study[1],
                studyName: study[2],
                studyDesc: study[3],
                sessionCount: study[4],
                role: study[5],
                canEdit: canEdit,
              }
            }),
          )
        }
      } catch (error) {
        console.error('Error retrieving studies: ', error)
      }
    },

    openNewStudy() {
      const studyStore = useStudyStore()
      studyStore.clearStudyID()
      sessionStorage.removeItem('currentStudyID')
      studyStore.incrementFormResetKey()
      this.$router.push({ name: 'StudyForm' })
    },

    calculateProgress(sessionCount) {
      const [completed, expected] = sessionCount.split('/').map(Number)
      let percentVal = Math.floor((completed / expected) * 100)
      return percentVal
    },

    openDrawer(studyID) {
      const match = this.studies.find(study => study.studyID == studyID)
      if (match) {
        const studyStore = useStudyStore()

        this.selectedStudy = match
        this.drawer = true
        studyStore.setDrawerStudyID(match.studyID)
      }
    },

    async downloadStudyData(studyID) {
      try {
        const path = `/get_all_session_data_instance_zip`
        const response = await api.post(
          path,
          { study_id: studyID },
          { responseType: 'blob' },
        )

        const disposition = response.headers['content-disposition']
        const filename = disposition
          ? disposition.split('filename=')[1].replace(/"/g, '')
          : 'download.zip'

        const blob = new Blob([response.data], { type: 'application/zip' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = filename
        link.click()
      } catch (error) {
        console.error('Error downloading study data:', error)
      }
    },

    async checkIfOverwriteAllowed(studyID) {
      try {
        const payload = { studyID: studyID } // Pass studyID in the request body
        const response = await api.post('/is_overwrite_study_allowed', payload)

        if (response.data === true) {
          return true
        } else {
          return false
        }
      } catch (error) {
        console.error('Error checking overwrite permission:', error)
        this.isButtonVisible = false
      }
    },

    async duplicateStudy(studyID) {
      try {
        const payload = { studyID: studyID }
        const response = await api.post('/copy_study', payload)

        // Refresh the page to show changes
        location.reload()
      } catch (error) {
        console.error('Error copying study', error)
      }
    },

    editExistingStudy(studyID) {
      const studyStore = useStudyStore()
      studyStore.setStudyID(studyID)
      studyStore.incrementFormResetKey()
      this.$router.push({ name: 'StudyForm' })
    },
  },
}
</script>

<style scoped>
.create-study {
  font-size: 16px;
  font-weight: bold;
  padding: 10px 20px;
  text-transform: none;
}

.study-name {
  display: flex;
  align-items: center;
}

.table-background {
  background-color: #ffffff !important;
}

.v-text-field {
  width: 100%;
}

.v-btn.block {
  width: 100%;
}

h2 {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 16px;
}

.mb-4 {
  margin-bottom: 16px !important;
}

.d-flex {
  display: flex !important;
}

.justify-end {
  justify-content: flex-end !important;
}
.v-dialog .v-text-field {
  margin-bottom: 16px;
}
.share-card {
  max-width: 640px;
  width: 100%;
  border-radius: 16px;
}

.share-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.people-access-label {
  font-weight: 600;
  font-size: 0.95rem;
  color: #444;
  margin-top: 10px;
}

.user-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.truncate-email {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.role-display {
  min-width: 80px;
  text-align: right;
  font-weight: 500;
  color: #444;
}
.role-select {
  min-width: 120px;
  max-width: 140px;
}

.v-avatar {
  flex-shrink: 0;
  margin-right: 12px;
}

.user-email {
  font-size: 0.95rem;
  color: #333;
  margin-right: 16px;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-weight: 500;
  min-width: 80px;
  text-align: right;
  color: #444;
}

.user-row {
  border-radius: 8px;
  transition: background-color 0.2s ease;
  padding: 4px 8px;
}

.user-row:hover {
  background-color: #f5f5f5;
}
/* maybe ditch this below idk */
.v-text-field,
.v-select {
  max-height: 44px;
}
.v-avatar img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}
</style>
