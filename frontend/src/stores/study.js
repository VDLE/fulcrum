import { defineStore } from 'pinia'

export const useStudyStore = defineStore('study', {
  state: () => ({
    currentStudyID: null, // Used when editing or creating a study
    drawerStudyID: null, // Used to reopen the drawer after navigating away
    sessionID: null, // Used by SessionReporting view
    formResetKey: 0, // Used to force remount of StudyForm
  }),

  actions: {
    // Restore all values from sessionStorage
    initializeFromSession() {
      const storedStudyID = sessionStorage.getItem('currentStudyID')
      const storedDrawerID = sessionStorage.getItem('drawerStudyID')
      const storedSessionID = sessionStorage.getItem('sessionID')

      if (storedStudyID !== null) this.currentStudyID = Number(storedStudyID)
      if (storedDrawerID !== null) this.drawerStudyID = Number(storedDrawerID)
      if (storedSessionID !== null) this.sessionID = Number(storedSessionID)
    },

    // STUDY ID
    setStudyID(id) {
      this.currentStudyID = id
      sessionStorage.setItem('currentStudyID', id)
    },
    clearStudyID() {
      this.currentStudyID = null
      sessionStorage.removeItem('currentStudyID')
    },

    // DRAWER STUDY ID
    setDrawerStudyID(id) {
      this.drawerStudyID = id
      sessionStorage.setItem('drawerStudyID', id)
    },
    clearDrawerStudyID() {
      this.drawerStudyID = null
      sessionStorage.removeItem('drawerStudyID')
    },

    // SESSION ID
    setSessionID(id) {
      this.sessionID = id
      sessionStorage.setItem('sessionID', id)
    },
    clearSessionID() {
      this.sessionID = null
      sessionStorage.removeItem('sessionID')
    },

    // Remount trigger
    incrementFormResetKey() {
      this.formResetKey++
    },

    // Optional: clear everything at once (e.g., on logout)
    reset() {
      this.clearStudyID()
      this.clearDrawerStudyID()
      this.clearSessionID()
      this.formResetKey = 0
    },
  },
})
