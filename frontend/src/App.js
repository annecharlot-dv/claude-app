import React, { Suspense, lazy } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { TenantProvider } from './contexts/TenantContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';
import performanceTracker from './utils/performance';
import './App.css';

// Lazy load components for better performance
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const CMSPages = lazy(() => import('./pages/cms/Pages'));
const PageEditor = lazy(() => import('./pages/cms/PageEditor'));
const Forms = lazy(() => import('./pages/Forms'));
const FormBuilder = lazy(() => import('./pages/FormBuilder'));
const Leads = lazy(() => import('./pages/Leads'));
const LeadDetail = lazy(() => import('./pages/LeadDetail'));
const Tours = lazy(() => import('./pages/Tours'));
const Settings = lazy(() => import('./pages/Settings'));

// Optimized QueryClient configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // Reduced retries for faster failure
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      // Enable background refetching for better UX
      refetchInterval: false,
      refetchIntervalInBackground: false,
    },
    mutations: {
      retry: 1,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

// Performance monitoring setup
React.useEffect(() => {
  // Track initial page load
  if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
      // Track page load time
      const navigation = performance.getEntriesByType('navigation')[0];
      if (navigation) {
        performanceTracker.recordMetric('PAGE_LOAD', navigation.loadEventEnd - navigation.fetchStart);
      }
      
      // Track bundle sizes
      performanceTracker.trackBundleSize();
      
      // Track memory usage periodically
      setInterval(() => {
        performanceTracker.trackMemoryUsage();
      }, 30000); // Every 30 seconds
    });
  }
}, []);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <BrowserRouter>
          <AuthProvider>
            <TenantProvider>
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route
                    path="/*"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Suspense fallback={<LoadingSpinner />}>
                            <Routes>
                              <Route path="/dashboard" element={<Dashboard />} />
                              <Route path="/cms/pages" element={<CMSPages />} />
                              <Route path="/cms/pages/new" element={<PageEditor />} />
                              <Route path="/cms/pages/:pageId/edit" element={<PageEditor />} />
                              <Route path="/forms" element={<Forms />} />
                              <Route path="/forms/new" element={<FormBuilder />} />
                              <Route path="/forms/:formId/edit" element={<FormBuilder />} />
                              <Route path="/leads" element={<Leads />} />
                              <Route path="/leads/:leadId" element={<LeadDetail />} />
                              <Route path="/tours" element={<Tours />} />
                              <Route path="/settings" element={<Settings />} />
                            </Routes>
                          </Suspense>
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </TenantProvider>
          </AuthProvider>
        </BrowserRouter>
      </div>
    </QueryClientProvider>
  );
}

export default App;