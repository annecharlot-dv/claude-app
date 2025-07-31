const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'tests/frontend/support/e2e.js',
    specPattern: 'tests/frontend/e2e/**/*.cy.{js,jsx,ts,tsx}',
    videosFolder: 'tests/frontend/videos',
    screenshotsFolder: 'tests/frontend/screenshots',
    fixturesFolder: 'tests/frontend/fixtures',
    
    setupNodeEvents(on, config) {
      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message)
          return null
        },
      })
    },
    
    env: {
      // Multi-tenant test configuration
      tenants: {
        coworking: 'http://coworking.localhost:3000',
        university: 'http://university.localhost:3000',
        hotel: 'http://hotel.localhost:3000'
      },
      
      // Test user credentials
      testUsers: {
        admin: {
          email: 'admin@test.com',
          password: 'testpassword'
        },
        member: {
          email: 'member@test.com', 
          password: 'testpassword'
        }
      }
    },
    
    // Performance testing thresholds
    defaultCommandTimeout: 10000,
    pageLoadTimeout: 30000,
    requestTimeout: 10000,
    responseTimeout: 30000,
    
    // Viewport settings for responsive testing
    viewportWidth: 1280,
    viewportHeight: 720,
    
    // Video and screenshot settings
    video: true,
    screenshotOnRunFailure: true,
    
    // Browser settings
    chromeWebSecurity: false,
    
    // Retry configuration
    retries: {
      runMode: 2,
      openMode: 0
    }
  },
  
  component: {
    devServer: {
      framework: 'create-react-app',
      bundler: 'webpack',
    },
    supportFile: 'tests/frontend/support/component.js',
    specPattern: 'tests/frontend/component/**/*.cy.{js,jsx,ts,tsx}',
    indexHtmlFile: 'tests/frontend/support/component-index.html'
  }
})