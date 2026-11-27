describe('Stats Engine', () => {
  it('calculates descriptive statistics using the live Fulcrum API', () => {
    // Observe the real request without replacing the backend response.
    cy.intercept('POST', '/api/stats/describe').as('describeSample')
    cy.visit('/stats')
    cy.get('textarea').type('2, 4, 4, 4{enter}5 5 7 9')
    cy.contains('button', 'Calculate').click()
    cy.wait('@describeSample').its('response.statusCode').should('eq', 200)

    cy.contains('th', /^Mean$/).siblings('td').should('have.text', '5')
    cy.contains('th', /^Median$/).siblings('td').should('have.text', '4.5')
    cy.contains('th', /^Mode$/).siblings('td').should('have.text', '4')
  })
})
