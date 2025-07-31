"""
Comprehensive health check system for multi-tenant SaaS platform
"""
import asyncio
import aiohttp
import time
from typing import Dict, List, Any
import json
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.base_url = os.getenv('HEALTH_CHECK_BASE_URL', 'https://your-domain.com')
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        self.tenant_subdomains = ['demo', 'coworking', 'university', 'hotel']
        self.critical_endpoints = [
            '/api/health',
            '/api/auth/verify',
            '/api/bookings/availability',
            '/api/cms/pages'
        ]
        
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # API Health Checks
        api_results = await self.check_api_endpoints()
        results['checks']['api'] = api_results
        
        # Multi-tenant Health Checks
        tenant_results = await self.check_tenant_isolation()
        results['checks']['tenants'] = tenant_results
        
        # Database Health Checks
        db_results = await self.check_database_health()
        results['checks']['database'] = db_results
        
        # Performance Checks
        perf_results = await self.check_performance_metrics()
        results['checks']['performance'] = perf_results
        
        # Determine overall status
        if any(check.get('status') == 'unhealthy' for check in results['checks'].values()):
            results['overall_status'] = 'unhealthy'
        elif any(check.get('status') == 'degraded' for check in results['checks'].values()):
            results['overall_status'] = 'degraded'
            
        # Send alerts if needed
        if results['overall_status'] != 'healthy':
            await self.send_alert(results)
            
        return results
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """Check critical API endpoints"""
        results = {
            'status': 'healthy',
            'endpoints': {},
            'response_times': []
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint in self.critical_endpoints:
                start_time = time.time()
                try:
                    async with session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                        response_time = (time.time() - start_time) * 1000
                        results['response_times'].append(response_time)
                        
                        results['endpoints'][endpoint] = {
                            'status_code': response.status,
                            'response_time_ms': round(response_time, 2),
                            'status': 'healthy' if response.status < 400 else 'unhealthy'
                        }
                        
                        if response.status >= 400:
                            results['status'] = 'unhealthy'
                            
                except asyncio.TimeoutError:
                    results['endpoints'][endpoint] = {
                        'status': 'timeout',
                        'response_time_ms': 10000,
                        'error': 'Request timeout'
                    }
                    results['status'] = 'unhealthy'
                except Exception as e:
                    results['endpoints'][endpoint] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    results['status'] = 'unhealthy'
        
        # Calculate average response time
        if results['response_times']:
            avg_response_time = sum(results['response_times']) / len(results['response_times'])
            results['avg_response_time_ms'] = round(avg_response_time, 2)
            
            # Mark as degraded if response times are high
            if avg_response_time > 2000:  # 2 seconds
                results['status'] = 'degraded'
        
        return results
    
    async def check_tenant_isolation(self) -> Dict[str, Any]:
        """Check multi-tenant isolation"""
        results = {
            'status': 'healthy',
            'tenants': {}
        }
        
        async with aiohttp.ClientSession() as session:
            for subdomain in self.tenant_subdomains:
                tenant_url = f"https://{subdomain}.your-domain.com"
                try:
                    async with session.get(f"{tenant_url}/api/health", timeout=5) as response:
                        tenant_data = await response.json()
                        
                        results['tenants'][subdomain] = {
                            'status': 'healthy' if response.status == 200 else 'unhealthy',
                            'tenant_id': tenant_data.get('tenant_id'),
                            'response_code': response.status
                        }
                        
                        # Verify tenant isolation
                        if tenant_data.get('tenant_id') != subdomain:
                            results['tenants'][subdomain]['isolation_error'] = True
                            results['status'] = 'unhealthy'
                            
                except Exception as e:
                    results['tenants'][subdomain] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    results['status'] = 'unhealthy'
        
        return results
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        results = {
            'status': 'healthy',
            'connection_time_ms': 0,
            'query_performance': {}
        }
        
        try:
            # Test database connection (implement based on your DB)
            start_time = time.time()
            
            # Simulate database health check
            await asyncio.sleep(0.1)  # Replace with actual DB check
            
            connection_time = (time.time() - start_time) * 1000
            results['connection_time_ms'] = round(connection_time, 2)
            
            if connection_time > 1000:  # 1 second
                results['status'] = 'degraded'
                
        except Exception as e:
            results['status'] = 'unhealthy'
            results['error'] = str(e)
        
        return results
    
    async def check_performance_metrics(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        results = {
            'status': 'healthy',
            'memory_usage': 0,
            'cpu_usage': 0,
            'active_connections': 0
        }
        
        try:
            # Get system metrics (implement based on your monitoring setup)
            # This is a placeholder - integrate with your actual monitoring
            results['memory_usage'] = 45.2  # percentage
            results['cpu_usage'] = 23.1     # percentage
            results['active_connections'] = 150
            
            # Set status based on thresholds
            if results['memory_usage'] > 90 or results['cpu_usage'] > 90:
                results['status'] = 'unhealthy'
            elif results['memory_usage'] > 75 or results['cpu_usage'] > 75:
                results['status'] = 'degraded'
                
        except Exception as e:
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    async def send_alert(self, health_results: Dict[str, Any]):
        """Send alert to monitoring service"""
        if not self.webhook_url:
            logger.warning("No webhook URL configured for alerts")
            return
        
        alert_data = {
            'timestamp': health_results['timestamp'],
            'status': health_results['overall_status'],
            'message': f"Health check failed: {health_results['overall_status']}",
            'details': health_results['checks']
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=alert_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Alert sent successfully")
                    else:
                        logger.error(f"Failed to send alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

async def main():
    """Main health check execution"""
    checker = HealthChecker()
    results = await checker.run_health_checks()
    
    print(json.dumps(results, indent=2))
    
    # Exit with error code if unhealthy
    if results['overall_status'] == 'unhealthy':
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())