/**
 * Optimized API Service
 * Implements caching, request deduplication, and performance tracking
 */
import axios from 'axios';
import performanceTracker from '../utils/performance';

// Request cache for deduplication
const requestCache = new Map();
const pendingRequests = new Map();

// Create optimized axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for performance tracking and caching
api.interceptors.request.use(
  (config) => {
    // Add performance tracking
    config.metadata = { startTime: performance.now() };
    
    // Add tenant ID from localStorage if available
    const tenantId = localStorage.getItem('tenantId');
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
    
    // Add auth token
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for performance tracking and caching
api.interceptors.response.use(
  (response) => {
    // Track API call performance
    const duration = performance.now() - response.config.metadata.startTime;
    performanceTracker.recordMetric('API_CALL', duration, {
      url: response.config.url,
      method: response.config.method.toUpperCase(),
      status: response.status,
      success: true
    });
    
    // Cache GET responses
    if (response.config.method === 'get' && response.status === 200) {
      const cacheKey = `${response.config.method}:${response.config.url}`;
      const cacheEntry = {
        data: response.data,
        timestamp: Date.now(),
        etag: response.headers.etag
      };
      
      // Cache for 5 minutes by default
      const cacheDuration = getCacheDuration(response.config.url);
      if (cacheDuration > 0) {
        requestCache.set(cacheKey, cacheEntry);
        
        // Auto-cleanup cache entry
        setTimeout(() => {
          requestCache.delete(cacheKey);
        }, cacheDuration);
      }
    }
    
    return response;
  },
  (error) => {
    // Track API errors
    const duration = error.config ? 
      performance.now() - error.config.metadata.startTime : 0;
    
    performanceTracker.recordMetric('API_ERROR', duration, {
      url: error.config?.url || 'unknown',
      method: error.config?.method?.toUpperCase() || 'unknown',
      status: error.response?.status || 0,
      error: error.message
    });
    
    return Promise.reject(error);
  }
);

// Get cache duration based on URL
function getCacheDuration(url) {
  const cacheDurations = {
    '/cms/templates': 60 * 60 * 1000, // 1 hour
    '/cms/pages': 30 * 60 * 1000,     // 30 minutes
    '/forms': 30 * 60 * 1000,         // 30 minutes
    '/leads': 5 * 60 * 1000,          // 5 minutes
    '/tours/slots': 10 * 60 * 1000,   // 10 minutes
  };
  
  for (const [pattern, duration] of Object.entries(cacheDurations)) {
    if (url.includes(pattern)) {
      return duration;
    }
  }
  
  return 0; // No caching by default
}

// Enhanced request function with caching and deduplication
async function makeRequest(config) {
  const cacheKey = `${config.method}:${config.url}`;
  
  // Check cache for GET requests
  if (config.method === 'get') {
    const cached = requestCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < getCacheDuration(config.url)) {
      // Return cached response
      performanceTracker.recordMetric('API_CACHE_HIT', 0, {
        url: config.url,
        method: 'GET'
      });
      
      return { data: cached.data, fromCache: true };
    }
  }
  
  // Check for pending identical requests (deduplication)
  if (pendingRequests.has(cacheKey)) {
    return pendingRequests.get(cacheKey);
  }
  
  // Make the request
  const requestPromise = api(config);
  
  // Store pending request for deduplication
  pendingRequests.set(cacheKey, requestPromise);
  
  try {
    const response = await requestPromise;
    return response;
  } finally {
    // Clean up pending request
    pendingRequests.delete(cacheKey);
  }
}

// API service methods
export const apiService = {
  // Authentication
  async login(credentials) {
    const response = await makeRequest({
      method: 'post',
      url: '/auth/login',
      data: credentials,
      params: { tenant_subdomain: window.location.hostname.split('.')[0] }
    });
    return response.data;
  },

  async register(userData) {
    const response = await makeRequest({
      method: 'post',
      url: '/auth/register',
      data: userData,
      params: { tenant_subdomain: window.location.hostname.split('.')[0] }
    });
    return response.data;
  },

  // CMS Pages
  async getPages(params = {}) {
    const response = await makeRequest({
      method: 'get',
      url: '/cms/pages',
      params
    });
    return response.data;
  },

  async getPage(pageId) {
    const response = await makeRequest({
      method: 'get',
      url: `/cms/pages/${pageId}`
    });
    return response.data;
  },

  async createPage(pageData) {
    const response = await makeRequest({
      method: 'post',
      url: '/cms/pages',
      data: pageData
    });
    
    // Invalidate pages cache
    this.invalidateCache('/cms/pages');
    
    return response.data;
  },

  async updatePage(pageId, pageData) {
    const response = await makeRequest({
      method: 'put',
      url: `/cms/pages/${pageId}`,
      data: pageData
    });
    
    // Invalidate related caches
    this.invalidateCache('/cms/pages');
    this.invalidateCache(`/cms/pages/${pageId}`);
    
    return response.data;
  },

  async deletePage(pageId) {
    const response = await makeRequest({
      method: 'delete',
      url: `/cms/pages/${pageId}`
    });
    
    // Invalidate related caches
    this.invalidateCache('/cms/pages');
    this.invalidateCache(`/cms/pages/${pageId}`);
    
    return response.data;
  },

  // Forms
  async getForms() {
    const response = await makeRequest({
      method: 'get',
      url: '/forms'
    });
    return response.data;
  },

  async createForm(formData) {
    const response = await makeRequest({
      method: 'post',
      url: '/forms',
      data: formData
    });
    
    this.invalidateCache('/forms');
    return response.data;
  },

  async submitForm(formId, formData) {
    const response = await makeRequest({
      method: 'post',
      url: `/forms/${formId}/submit`,
      data: formData
    });
    return response.data;
  },

  // Leads
  async getLeads(params = {}) {
    const response = await makeRequest({
      method: 'get',
      url: '/leads',
      params
    });
    return response.data;
  },

  async getLead(leadId) {
    const response = await makeRequest({
      method: 'get',
      url: `/leads/${leadId}`
    });
    return response.data;
  },

  async createLead(leadData) {
    const response = await makeRequest({
      method: 'post',
      url: '/leads',
      data: leadData
    });
    
    this.invalidateCache('/leads');
    return response.data;
  },

  async updateLead(leadId, leadData) {
    const response = await makeRequest({
      method: 'put',
      url: `/leads/${leadId}`,
      data: leadData
    });
    
    this.invalidateCache('/leads');
    this.invalidateCache(`/leads/${leadId}`);
    
    return response.data;
  },

  // Tours
  async getTourSlots(params = {}) {
    const response = await makeRequest({
      method: 'get',
      url: '/tours/slots',
      params
    });
    return response.data;
  },

  async bookTour(tourData) {
    const response = await makeRequest({
      method: 'post',
      url: '/tours/book',
      data: tourData
    });
    
    this.invalidateCache('/tours/slots');
    return response.data;
  },

  // Performance monitoring
  async getPerformanceMetrics(hours = 1) {
    const response = await makeRequest({
      method: 'get',
      url: '/performance/metrics',
      params: { hours }
    });
    return response.data;
  },

  async getCacheStats() {
    const response = await makeRequest({
      method: 'get',
      url: '/performance/cache/stats'
    });
    return response.data;
  },

  // Cache management
  invalidateCache(pattern) {
    // Remove matching entries from local cache
    for (const [key] of requestCache.entries()) {
      if (key.includes(pattern)) {
        requestCache.delete(key);
      }
    }
  },

  clearCache() {
    requestCache.clear();
    pendingRequests.clear();
  },

  // Get cache statistics
  getCacheInfo() {
    return {
      cacheSize: requestCache.size,
      pendingRequests: pendingRequests.size,
      cacheEntries: Array.from(requestCache.keys())
    };
  }
};

export default apiService;