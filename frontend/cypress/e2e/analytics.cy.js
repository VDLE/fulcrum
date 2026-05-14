// Test file for the analytics functionality

describe('Analytics Dashboard', () => {
    beforeEach(() => {
      // Set up API mocks
      cy.intercept('GET', '/api/studies', { fixture: 'studies.json' }).as('getStudies');
      cy.intercept('GET', '/api/analytics/*/summary', { fixture: 'analytics-summary.json' }).as('getSummary');
      cy.intercept('GET', '/api/analytics/*/learning-curve', { fixture: 'learning-curve.json' }).as('getLearningCurve');
      cy.intercept('GET', '/api/analytics/*/completion-rate', { fixture: 'completion-rate.json' }).as('getCompletionRate');
      cy.intercept('GET', '/api/analytics/*/timeline', { fixture: 'timeline.json' }).as('getTimeline');
      cy.intercept('GET', '/api/analytics/*/task-performance', { fixture: 'task-performance.json' }).as('getTaskPerformance');
      cy.intercept('GET', '/api/analytics/*/participants', { fixture: 'participants.json' }).as('getParticipants');
      cy.intercept('GET', '/api/analytics/*/interaction-density', { fixture: 'interaction-density.json' }).as('getInteractionDensity');
      cy.intercept('GET', '/api/analytics/*/statistics', { fixture: 'statistics.json' }).as('getStatistics');
      
      // Visit the analytics page
      cy.visit('/data-analytics');
    });
    
    it('should load and display the analytics dashboard', () => {
      // Check the title is visible
      cy.contains('h1', 'Analytics Workspace').should('be.visible');
      
      // Check for study selector
      cy.get('select').should('exist');
      
      // Initial state should show the no-selection message
      cy.contains('Select a Study').should('be.visible');
    });
    
    it('should load data when a study is selected', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getLearningCurve', '@getCompletionRate', '@getTimeline', '@getTaskPerformance']);
      
      // Verify summary cards are visible
      cy.get('.summary-row').should('be.visible');
      cy.get('.summary-row').find('.summary-card').should('have.length.at.least', 3);
      
      // Check that charts are visible
      cy.get('.charts-container').should('be.visible');
    });
    
    it('should navigate between tabs correctly', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getLearningCurve', '@getCompletionRate', '@getTimeline', '@getTaskPerformance']);
      
      // Check Overview tab is active by default
      cy.contains('button', 'Overview').should('have.class', 'v-tab--active');
      
      // Navigate to Task Analysis tab
      cy.contains('button', 'Task Analysis').click();
      cy.wait('@getTaskPerformance');
      cy.contains('Task Performance Comparison').should('be.visible');
      
      // Navigate to Participants tab
      cy.contains('button', 'Participants').click();
      cy.wait('@getParticipants');
      cy.contains('Participant Data').should('be.visible');
      
      // Navigate to Interaction Data tab
      cy.contains('button', 'Interaction Data').click();
      cy.wait('@getInteractionDensity');
      cy.contains('Interaction Density Analysis').should('be.visible');
      
      // Navigate to Advanced Statistics tab
      cy.contains('button', 'Advanced Statistics').click();
      cy.wait('@getStatistics');
      cy.contains('Statistical Analysis').should('be.visible');
    });
    
    it('should refresh data when refresh button is clicked', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for initial API calls to complete
      cy.wait(['@getSummary', '@getLearningCurve', '@getCompletionRate', '@getTimeline', '@getTaskPerformance']);
      
      // Click refresh button
      cy.contains('button', 'Refresh').click();
      
      // Verify API calls are made again
      cy.wait(['@getSummary', '@getLearningCurve', '@getCompletionRate', '@getTimeline', '@getTaskPerformance']);
    });
    
    it('should show learning curve chart with correct data', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getLearningCurve']);
      
      // Check learning curve chart is visible
      cy.contains('Learning Curve').should('be.visible');
      cy.get('.chart-content').should('be.visible');
      
      // Toggle between "All Tasks" and "By Task" views
      cy.contains('button', 'All Tasks').click();
      cy.contains('button', 'By Task').click();
      
      // Chart should update without errors
      cy.get('.chart-error').should('not.exist');
    });
    
    it('should show task performance comparison with correct data', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getTaskPerformance']);
      
      // Navigate to Task Analysis tab
      cy.contains('button', 'Task Analysis').click();
      
      // Check task performance comparison is visible
      cy.contains('Task Performance Comparison').should('be.visible');
      
      // Toggle between different metrics
      cy.contains('button', 'Time').click();
      cy.contains('button', 'Success').click();
      cy.contains('button', 'Errors').click();
      
      // Chart should update without errors
      cy.get('.chart-error').should('not.exist');
    });
    
    it('should show participant data table with search functionality', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getParticipants']);
      
      // Navigate to Participants tab
      cy.contains('button', 'Participants').click();
      
      // Check participant table is visible
      cy.contains('Participant Data').should('be.visible');
      cy.get('.participant-table').should('be.visible');
      
      // Test search functionality
      cy.get('.search-field input').type('P001');
      
      // Table should filter results
      cy.get('.participant-table tbody tr').should('have.length.lessThan', 10);
      
      // Clear search
      cy.get('.search-field input').clear();
      
      // Table should show all results again
      cy.get('.participant-table tbody tr').should('have.length.at.least', 1);
    });
    
    it('should show statistical analysis with multiple tabs', () => {
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for API calls to complete
      cy.wait(['@getSummary', '@getStatistics']);
      
      // Navigate to Advanced Statistics tab
      cy.contains('button', 'Advanced Statistics').click();
      
      // Check statistical analysis is visible
      cy.contains('Statistical Analysis').should('be.visible');
      
      // Navigate through statistical analysis tabs
      cy.contains('button', 'ANOVA').should('have.class', 'v-btn--active');
      
      cy.contains('button', 'T-Tests').click();
      cy.contains('Group Comparison').should('be.visible');
      
      cy.contains('button', 'Correlations').click();
      cy.contains('Correlation Analysis').should('be.visible');
      
      cy.contains('button', 'Regression').click();
      cy.contains('Regression Analysis').should('be.visible');
      
      cy.contains('button', 'Outliers').click();
      cy.contains('Outlier Detection').should('be.visible');
    });
    
    it('should handle API errors gracefully', () => {
      // Override API intercept to return an error
      cy.intercept('GET', '/api/analytics/*/summary', {
        statusCode: 500,
        body: { error: 'Internal Server Error' }
      }).as('getSummaryError');
      
      // Select the first study
      cy.get('select').select(1);
      
      // Wait for error response
      cy.wait('@getSummaryError');
      
      // Check error message is displayed
      cy.contains('Failed to load analytics data').should('be.visible');
      
      // Try again button should be visible
      cy.contains('button', 'Try Again').should('be.visible');
    });
  });