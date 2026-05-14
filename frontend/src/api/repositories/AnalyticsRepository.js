import Repository from './Repository'
import analyticsApi from '../analyticsApi'

// Repository for analytics data
export default class AnalyticsRepository extends Repository {
  constructor() {
    super()
    this.apiClient = analyticsApi
  }

  // Get all available studies
  async findAllStudies() {
    try {
      return await this.apiClient.getStudies()
    } catch (error) {
      console.error('Error fetching studies:', error)
      return []
    }
  }

  // Get summary data for a study
  // studyId - Study identifier
  async getStudySummary(studyId) {
    try {
      return await this.apiClient.getSummaryMetrics(studyId)
    } catch (error) {
      console.error(`Error fetching summary for study ${studyId}:`, error)
      return {}
    }
  }

  // Get learning curve data
  // studyId - Study identifier
  async getLearningCurveData(studyId) {
    try {
      return await this.apiClient.getLearningCurveData(studyId)
    } catch (error) {
      console.error(
        `Error fetching learning curve data for study ${studyId}:`,
        error,
      )
      return []
    }
  }

  // Get task performance comparison data
  // studyId - Study identifier
  async getTaskPerformanceData(studyId) {
    try {
      return await this.apiClient.getTaskPerformanceData(studyId)
    } catch (error) {
      console.error(
        `Error fetching task performance data for study ${studyId}:`,
        error,
      )
      return []
    }
  }

  // Get participant data for a study
  // studyId - Study identifier
  async getParticipantData(studyId) {
    try {
      return await this.apiClient.getParticipantData(studyId)
    } catch (error) {
      console.error(
        `Error fetching participant data for study ${studyId}:`,
        error,
      )
      return []
    }
  }

  // Export study data to file
  // studyId - Study identifier
  // format - Export format (csv, json)
  async exportStudyData(studyId, format = 'csv') {
    try {
      return await this.apiClient.exportStudyData(studyId, format)
    } catch (error) {
      console.error(`Error exporting data for study ${studyId}:`, error)
      throw error
    }
  }

  // Methods from Repository interface
  // (analytics data is read-only)
  async findAll() {
    return this.findAllStudies()
  }

  async findById(id) {
    return this.getStudySummary(id)
  }

  async save() {
    throw new Error('Analytics data is read-only and cannot be saved')
  }

  async delete() {
    throw new Error('Analytics data is read-only and cannot be deleted')
  }
}
