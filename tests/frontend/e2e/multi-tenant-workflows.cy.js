/**
 * End-to-end tests for multi-tenant workflows
 */

describe('Multi-Tenant Workflows', () => {
  const tenants = Cypress.env('tenants')
  const testUsers = Cypress.env('testUsers')
  
  beforeEach(() => {
    // Clear cookies and local storage
    cy.clearCookies()
    cy.clearLocalStorage()
  })

  describe('Coworking Space Workflows', () => {
    beforeEach(() => {
      cy.visit(tenants.coworking)
    })

    it('should complete member booking workflow', () => {
      // Login as member
      cy.get('[data-cy=login-email]').type(testUsers.member.email)
      cy.get('[data-cy=login-password]').type(testUsers.member.password)
      cy.get('[data-cy=login-submit]').click()
      
      // Verify login success
      cy.url().should('include', '/dashboard')
      cy.get('[data-cy=user-menu]').should('contain', 'Member')
      
      // Navigate to booking page
      cy.get('[data-cy=nav-bookings]').click()
      cy.url().should('include', '/bookings')
      
      // Search for available spaces
      cy.get('[data-cy=booking-date]').type('2024-12-15')
      cy.get('[data-cy=booking-start-time]').select('10:00')
      cy.get('[data-cy=booking-end-time]').select('11:00')
      cy.get('[data-cy=search-spaces]').click()
      
      // Select a space
      cy.get('[data-cy=space-card]').first().click()
      cy.get('[data-cy=book-space]').click()
      
      // Fill booking details
      cy.get('[data-cy=booking-purpose]').type('Team standup meeting')
      cy.get('[data-cy=confirm-booking]').click()
      
      // Verify booking confirmation
      cy.get('[data-cy=booking-success]').should('be.visible')
      cy.get('[data-cy=booking-confirmation]').should('contain', 'confirmed')
      
      // Check booking appears in user's bookings
      cy.get('[data-cy=my-bookings]').click()
      cy.get('[data-cy=booking-list]').should('contain', 'Team standup meeting')
    })

    it('should handle booking conflicts gracefully', () => {
      cy.login(testUsers.member.email, testUsers.member.password)
      
      // Try to book an already occupied slot
      cy.get('[data-cy=nav-bookings]').click()
      cy.get('[data-cy=booking-date]').type('2024-12-15')
      cy.get('[data-cy=booking-start-time]').select('14:00')
      cy.get('[data-cy=booking-end-time]').select('15:00')
      cy.get('[data-cy=search-spaces]').click()
      
      // Should show no available spaces or conflict message
      cy.get('[data-cy=no-spaces-available]').should('be.visible')
        .or(cy.get('[data-cy=conflict-message]').should('be.visible'))
    })

    it('should display coworking-specific terminology', () => {
      cy.visit(tenants.coworking)
      
      // Check for coworking-specific terms
      cy.get('body').should('contain', 'Workspace')
      cy.get('body').should('contain', 'Member')
      cy.get('body').should('contain', 'Community')
      
      // Should not contain other industry terms
      cy.get('body').should('not.contain', 'Guest')
      cy.get('body').should('not.contain', 'Student')
      cy.get('body').should('not.contain', 'Room')
    })
  })

  describe('University Workflows', () => {
    beforeEach(() => {
      cy.visit(tenants.university)
    })

    it('should display university-specific interface', () => {
      // Check for university-specific terminology
      cy.get('body').should('contain', 'Classroom')
      cy.get('body').should('contain', 'Student')
      cy.get('body').should('contain', 'Course')
      
      // Should not contain other industry terms
      cy.get('body').should('not.contain', 'Workspace')
      cy.get('body').should('not.contain', 'Guest')
    })

    it('should handle academic calendar restrictions', () => {
      cy.login(testUsers.member.email, testUsers.member.password)
      
      // Try to book during exam period
      cy.get('[data-cy=nav-bookings]').click()
      cy.get('[data-cy=booking-date]').type('2024-12-10') // During exam period
      cy.get('[data-cy=booking-start-time]').select('10:00')
      cy.get('[data-cy=booking-end-time]').select('11:00')
      cy.get('[data-cy=search-spaces]').click()
      
      // Should show restriction message
      cy.get('[data-cy=exam-period-restriction]').should('be.visible')
    })

    it('should support recurring class bookings', () => {
      cy.login(testUsers.admin.email, testUsers.admin.password)
      
      // Navigate to recurring bookings
      cy.get('[data-cy=nav-admin]').click()
      cy.get('[data-cy=recurring-bookings]').click()
      
      // Create recurring booking
      cy.get('[data-cy=create-recurring]').click()
      cy.get('[data-cy=course-code]').type('CS101')
      cy.get('[data-cy=course-name]').type('Introduction to Computer Science')
      cy.get('[data-cy=recurring-days]').check(['monday', 'wednesday', 'friday'])
      cy.get('[data-cy=start-date]').type('2024-08-26')
      cy.get('[data-cy=end-date]').type('2024-12-06')
      cy.get('[data-cy=create-recurring-booking]').click()
      
      // Verify recurring booking created
      cy.get('[data-cy=recurring-success]').should('be.visible')
    })
  })

  describe('Hotel Workflows', () => {
    beforeEach(() => {
      cy.visit(tenants.hotel)
    })

    it('should display hotel-specific interface', () => {
      // Check for hotel-specific terminology
      cy.get('body').should('contain', 'Room')
      cy.get('body').should('contain', 'Guest')
      cy.get('body').should('contain', 'Reservation')
      
      // Should not contain other industry terms
      cy.get('body').should('not.contain', 'Workspace')
      cy.get('body').should('not.contain', 'Student')
    })

    it('should handle multi-night reservations', () => {
      // Navigate to booking page
      cy.get('[data-cy=nav-reservations]').click()
      
      // Fill reservation details
      cy.get('[data-cy=check-in-date]').type('2024-12-15')
      cy.get('[data-cy=check-out-date]').type('2024-12-18')
      cy.get('[data-cy=guest-count]').select('2')
      cy.get('[data-cy=room-type]').select('Standard')
      cy.get('[data-cy=search-rooms]').click()
      
      // Select room
      cy.get('[data-cy=room-card]').first().click()
      cy.get('[data-cy=book-room]').click()
      
      // Fill guest information
      cy.get('[data-cy=guest-name]').type('John Doe')
      cy.get('[data-cy=guest-email]').type('john.doe@email.com')
      cy.get('[data-cy=guest-phone]').type('+1234567890')
      
      // Process payment
      cy.get('[data-cy=payment-method]').select('Credit Card')
      cy.get('[data-cy=card-number]').type('4111111111111111')
      cy.get('[data-cy=card-expiry]').type('12/25')
      cy.get('[data-cy=card-cvv]').type('123')
      cy.get('[data-cy=confirm-reservation]').click()
      
      // Verify reservation confirmation
      cy.get('[data-cy=reservation-success]').should('be.visible')
      cy.get('[data-cy=confirmation-number]').should('be.visible')
    })

    it('should calculate correct pricing for different seasons', () => {
      cy.get('[data-cy=nav-reservations]').click()
      
      // Check peak season pricing
      cy.get('[data-cy=check-in-date]').type('2024-07-15') // Peak season
      cy.get('[data-cy=check-out-date]').type('2024-07-18')
      cy.get('[data-cy=search-rooms]').click()
      
      cy.get('[data-cy=room-price]').first().then(($price) => {
        const peakPrice = parseFloat($price.text().replace('$', ''))
        
        // Check low season pricing
        cy.get('[data-cy=check-in-date]').clear().type('2024-01-15') // Low season
        cy.get('[data-cy=check-out-date]').clear().type('2024-01-18')
        cy.get('[data-cy=search-rooms]').click()
        
        cy.get('[data-cy=room-price]').first().then(($lowPrice) => {
          const lowPrice = parseFloat($lowPrice.text().replace('$', ''))
          
          // Peak season should be more expensive
          expect(peakPrice).to.be.greaterThan(lowPrice)
        })
      })
    })
  })

  describe('Cross-Tenant Security', () => {
    it('should prevent cross-tenant data access', () => {
      // Login to coworking tenant
      cy.visit(tenants.coworking)
      cy.login(testUsers.member.email, testUsers.member.password)
      
      // Try to access university tenant with coworking session
      cy.visit(tenants.university)
      
      // Should be redirected to login or show access denied
      cy.url().should('include', '/login')
        .or(cy.get('[data-cy=access-denied]').should('be.visible'))
    })

    it('should maintain separate sessions per tenant', () => {
      // Login to coworking
      cy.visit(tenants.coworking)
      cy.login(testUsers.member.email, testUsers.member.password)
      cy.get('[data-cy=user-menu]').should('be.visible')
      
      // Visit university in same browser
      cy.visit(tenants.university)
      
      // Should not be logged in to university
      cy.get('[data-cy=login-form]').should('be.visible')
    })
  })

  describe('Performance Testing', () => {
    it('should load pages within performance thresholds', () => {
      const performanceThresholds = {
        pageLoad: 3000, // 3 seconds
        apiResponse: 1000 // 1 second
      }
      
      // Test coworking page load time
      const startTime = Date.now()
      cy.visit(tenants.coworking)
      cy.get('[data-cy=main-content]').should('be.visible').then(() => {
        const loadTime = Date.now() - startTime
        expect(loadTime).to.be.lessThan(performanceThresholds.pageLoad)
      })
    })

    it('should handle concurrent user actions', () => {
      // Simulate multiple rapid actions
      cy.visit(tenants.coworking)
      cy.login(testUsers.member.email, testUsers.member.password)
      
      // Rapid navigation
      for (let i = 0; i < 5; i++) {
        cy.get('[data-cy=nav-bookings]').click()
        cy.get('[data-cy=nav-dashboard]').click()
      }
      
      // Should remain responsive
      cy.get('[data-cy=user-menu]').should('be.visible')
    })
  })

  describe('Accessibility Testing', () => {
    it('should meet accessibility standards', () => {
      cy.visit(tenants.coworking)
      cy.injectAxe()
      cy.checkA11y()
    })

    it('should support keyboard navigation', () => {
      cy.visit(tenants.coworking)
      
      // Tab through navigation
      cy.get('body').tab()
      cy.focused().should('have.attr', 'data-cy', 'nav-home')
      
      cy.focused().tab()
      cy.focused().should('have.attr', 'data-cy', 'nav-bookings')
      
      // Enter key should activate links
      cy.focused().type('{enter}')
      cy.url().should('include', '/bookings')
    })
  })
})

// Custom commands
Cypress.Commands.add('login', (email, password) => {
  cy.get('[data-cy=login-email]').type(email)
  cy.get('[data-cy=login-password]').type(password)
  cy.get('[data-cy=login-submit]').click()
  cy.get('[data-cy=user-menu]').should('be.visible')
})