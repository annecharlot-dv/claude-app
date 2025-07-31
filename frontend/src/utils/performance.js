/**
 * Frontend Performance Utilities
 * Implements Core Web Vitals monitoring and optimization helpers
 */

// Performance monitoring
class PerformanceTracker {
  constructor() {
    this.metrics = new Map();
    this.observers = new Map();
    this.initializeObservers();
  }

  initializeObservers() {
    // Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.recordMetric('LCP', lastEntry.startTime);
      });
      
      try {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.set('lcp', lcpObserver);
      } catch (e) {
        console.warn('LCP observer not supported');
      }

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          this.recordMetric('FID', entry.processingStart - entry.startTime);
        });
      });
      
      try {
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.set('fid', fidObserver);
      } catch (e) {
        console.warn('FID observer not supported');
      }

      // Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            this.recordMetric('CLS', clsValue);
          }
        });
      });
      
      try {
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.set('cls', clsObserver);
      } catch (e) {
        console.warn('CLS observer not supported');
      }

      // Long Tasks
      const longTaskObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        entries.forEach((entry) => {
          this.recordMetric('LONG_TASK', entry.duration);
        });
      });
      
      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.set('longtask', longTaskObserver);
      } catch (e) {
        console.warn('Long task observer not supported');
      }
    }
  }

  recordMetric(name, value, metadata = {}) {
    const metric = {
      name,
      value,
      timestamp: Date.now(),
      url: window.location.pathname,
      ...metadata
    };

    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    
    this.metrics.get(name).push(metric);

    // Send to analytics if configured
    this.sendToAnalytics(metric);

    // Log performance issues
    this.checkThresholds(metric);
  }

  checkThresholds(metric) {
    const thresholds = {
      LCP: 2500, // 2.5s
      FID: 100,  // 100ms
      CLS: 0.1,  // 0.1
      LONG_TASK: 50 // 50ms
    };

    const threshold = thresholds[metric.name];
    if (threshold && metric.value > threshold) {
      console.warn(`Performance issue detected: ${metric.name} = ${metric.value} (threshold: ${threshold})`);
      
      // Send alert to monitoring system
      this.sendAlert(metric, threshold);
    }
  }

  sendToAnalytics(metric) {
    // Send to your analytics service
    if (window.gtag) {
      window.gtag('event', 'performance_metric', {
        metric_name: metric.name,
        metric_value: metric.value,
        page_path: metric.url
      });
    }
  }

  sendAlert(metric, threshold) {
    // Send performance alert to backend
    fetch('/api/performance/alert', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        metric: metric.name,
        value: metric.value,
        threshold,
        url: metric.url,
        timestamp: metric.timestamp
      })
    }).catch(err => console.warn('Failed to send performance alert:', err));
  }

  getMetrics() {
    const summary = {};
    
    this.metrics.forEach((values, name) => {
      const latest = values[values.length - 1];
      const avg = values.reduce((sum, m) => sum + m.value, 0) / values.length;
      
      summary[name] = {
        latest: latest.value,
        average: avg,
        count: values.length,
        timestamp: latest.timestamp
      };
    });

    return summary;
  }

  disconnect() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }
}

// Resource loading optimization
export const loadResource = (url, type = 'script') => {
  return new Promise((resolve, reject) => {
    const startTime = performance.now();
    
    let element;
    if (type === 'script') {
      element = document.createElement('script');
      element.src = url;
      element.async = true;
    } else if (type === 'style') {
      element = document.createElement('link');
      element.rel = 'stylesheet';
      element.href = url;
    }

    element.onload = () => {
      const loadTime = performance.now() - startTime;
      performanceTracker.recordMetric('RESOURCE_LOAD', loadTime, { url, type });
      resolve();
    };

    element.onerror = () => {
      const loadTime = performance.now() - startTime;
      performanceTracker.recordMetric('RESOURCE_ERROR', loadTime, { url, type });
      reject(new Error(`Failed to load ${type}: ${url}`));
    };

    document.head.appendChild(element);
  });
};

// Image lazy loading with performance tracking
export const createLazyImage = (src, alt = '', className = '') => {
  const img = document.createElement('img');
  img.alt = alt;
  img.className = className;
  img.loading = 'lazy';
  
  const startTime = performance.now();
  
  img.onload = () => {
    const loadTime = performance.now() - startTime;
    performanceTracker.recordMetric('IMAGE_LOAD', loadTime, { src });
  };

  img.onerror = () => {
    const loadTime = performance.now() - startTime;
    performanceTracker.recordMetric('IMAGE_ERROR', loadTime, { src });
  };

  // Use Intersection Observer for better lazy loading
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          img.src = src;
          observer.unobserve(img);
        }
      });
    }, { threshold: 0.1 });

    observer.observe(img);
  } else {
    // Fallback for older browsers
    img.src = src;
  }

  return img;
};

// Bundle size tracking
export const trackBundleSize = () => {
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name.includes('.js') || entry.name.includes('.css')) {
          performanceTracker.recordMetric('BUNDLE_SIZE', entry.transferSize, {
            name: entry.name,
            type: entry.name.includes('.js') ? 'javascript' : 'css'
          });
        }
      });
    });

    observer.observe({ entryTypes: ['resource'] });
  }
};

// Memory usage tracking
export const trackMemoryUsage = () => {
  if ('memory' in performance) {
    const memory = performance.memory;
    performanceTracker.recordMetric('MEMORY_USED', memory.usedJSHeapSize);
    performanceTracker.recordMetric('MEMORY_TOTAL', memory.totalJSHeapSize);
    performanceTracker.recordMetric('MEMORY_LIMIT', memory.jsHeapSizeLimit);
  }
};

// API call performance tracking
export const trackApiCall = async (url, options = {}) => {
  const startTime = performance.now();
  
  try {
    const response = await fetch(url, options);
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    performanceTracker.recordMetric('API_CALL', duration, {
      url,
      method: options.method || 'GET',
      status: response.status,
      success: response.ok
    });
    
    return response;
  } catch (error) {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    performanceTracker.recordMetric('API_ERROR', duration, {
      url,
      method: options.method || 'GET',
      error: error.message
    });
    
    throw error;
  }
};

// React component performance HOC
export const withPerformanceTracking = (WrappedComponent, componentName) => {
  return function PerformanceTrackedComponent(props) {
    const startTime = performance.now();
    
    React.useEffect(() => {
      const renderTime = performance.now() - startTime;
      performanceTracker.recordMetric('COMPONENT_RENDER', renderTime, {
        component: componentName
      });
    });

    return React.createElement(WrappedComponent, props);
  };
};

// Initialize performance tracking
const performanceTracker = new PerformanceTracker();

// Export for global access
window.performanceTracker = performanceTracker;

export default performanceTracker;