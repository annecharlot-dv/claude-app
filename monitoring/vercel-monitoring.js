// Vercel Edge Functions for Real-time Monitoring
import { NextRequest, NextResponse } from 'next/server';

// Performance monitoring middleware
export async function middleware(request) {
  const start = Date.now();
  const response = NextResponse.next();
  
  // Add performance headers
  response.headers.set('X-Response-Time', `${Date.now() - start}ms`);
  response.headers.set('X-Tenant-ID', getTenantFromRequest(request));
  
  // Log performance metrics
  await logPerformanceMetrics(request, response, Date.now() - start);
  
  return response;
}

function getTenantFromRequest(request) {
  const host = request.headers.get('host') || '';
  const subdomain = host.split('.')[0];
  return subdomain !== 'www' ? subdomain : 'default';
}

async function logPerformanceMetrics(request, response, duration) {
  const metrics = {
    timestamp: new Date().toISOString(),
    tenant_id: getTenantFromRequest(request),
    path: request.nextUrl.pathname,
    method: request.method,
    duration_ms: duration,
    status_code: response.status,
    user_agent: request.headers.get('user-agent'),
    ip: request.ip || request.headers.get('x-forwarded-for'),
    region: process.env.VERCEL_REGION || 'unknown'
  };

  // Send to monitoring service (replace with your preferred service)
  try {
    await fetch(process.env.MONITORING_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(metrics)
    });
  } catch (error) {
    console.error('Failed to log metrics:', error);
  }
}

export const config = {
  matcher: [
    '/api/:path*',
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};