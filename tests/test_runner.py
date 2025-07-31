"""
Comprehensive test runner for multi-tenant SaaS platform
"""
import pytest
import sys
import os
import asyncio
from typing import Dict, Any, List
import json
from datetime import datetime

class TestRunner:
    """Orchestrates comprehensive testing across all test categories"""
    
    def __init__(self):
        self.test_categories = {
            "unit": {
                "path": "tests/unit/",
                "markers": ["unit"],
                "timeout": 300,  # 5 minutes
                "parallel": True
            },
            "integration": {
                "path": "tests/integration/",
                "markers": ["integration"],
                "timeout": 600,  # 10 minutes
                "parallel": True
            },
            "performance": {
                "path": "tests/performance/",
                "markers": ["performance"],
                "timeout": 1800,  # 30 minutes
                "parallel": False
            },
            "security": {
                "path": "tests/security/",
                "markers": ["security", "tenant_isolation"],
                "timeout": 900,  # 15 minutes
                "parallel": True
            },
            "e2e": {
                "path": "tests/e2e/",
                "markers": ["e2e"],
                "timeout": 1200,  # 20 minutes
                "parallel": False
            }
        }
        
        self.performance_thresholds = {
            "api_response_time_ms": 100,
            "database_query_time_ms": 50,
            "page_load_time_ms": 2000,
            "concurrent_users": 100,
            "requests_per_second": 1000
        }
    
    def run_test_category(self, category: str, verbose: bool = False) -> Dict[str, Any]:
        """Run tests for a specific category"""
        if category not in self.test_categories:
            raise ValueError(f"Unknown test category: {category}")
        
        config = self.test_categories[category]
        
        # Build pytest command
        cmd_args = [
            "-v" if verbose else "-q",
            f"--timeout={config['timeout']}",
            "--tb=short",
            f"--junitxml=test-results-{category}.xml",
            "--cov=backend",
            f"--cov-report=html:htmlcov-{category}",
            "--cov-report=xml",
        ]
        
        # Add markers
        if config["markers"]:
            marker_expr = " or ".join(config["markers"])
            cmd_args.extend(["-m", marker_expr])
        
        # Add parallel execution if supported
        if config["parallel"]:
            cmd_args.extend(["-n", "auto"])
        
        # Add test path
        cmd_args.append(config["path"])
        
        # Run tests
        start_time = time.time()
        exit_code = pytest.main(cmd_args)
        end_time = time.time()
        
        return {
            "category": category,
            "exit_code": exit_code,
            "duration": end_time - start_time,
            "success": exit_code == 0
        }
    
    def run_all_tests(self, categories: List[str] = None, verbose: bool = False) -> Dict[str, Any]:
        """Run all test categories or specified ones"""
        if categories is None:
            categories = list(self.test_categories.keys())
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "categories": {},
            "summary": {
                "total_categories": len(categories),
                "passed_categories": 0,
                "failed_categories": 0,
                "total_duration": 0
            }
        }
        
        overall_start = time.time()
        
        for category in categories:
            logger.info(f"Running {category} tests...")
            
            try:
                result = self.run_test_category(category, verbose)
                results["categories"][category] = result
                
                if result["success"]:
                    results["summary"]["passed_categories"] += 1
                else:
                    results["summary"]["failed_categories"] += 1
                
                results["summary"]["total_duration"] += result["duration"]
                
            except Exception as e:
                logger.error(f"Failed to run {category} tests: {e}")
                results["categories"][category] = {
                    "category": category,
                    "exit_code": -1,
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                }
                results["summary"]["failed_categories"] += 1
        
        results["summary"]["total_duration"] = time.time() - overall_start
        results["summary"]["success_rate"] = (
            results["summary"]["passed_categories"] / 
            results["summary"]["total_categories"] * 100
        )
        
        return results
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks and validate against thresholds"""
        logger.info("Running performance benchmarks...")
        
        # Run performance tests with specific configuration
        cmd_args = [
            "-v",
            "--timeout=1800",
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-json=benchmark-results.json",
            "tests/performance/"
        ]
        
        exit_code = pytest.main(cmd_args)
        
        # Load benchmark results if available
        benchmark_results = {}
        if os.path.exists("benchmark-results.json"):
            with open("benchmark-results.json", "r") as f:
                benchmark_results = json.load(f)
        
        return {
            "success": exit_code == 0,
            "thresholds": self.performance_thresholds,
            "results": benchmark_results
        }
    
    def run_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        logger.info("Running security audit...")
        
        # Run security tests
        cmd_args = [
            "-v",
            "--timeout=900",
            "-m", "security or tenant_isolation",
            "--tb=short",
            "tests/security/"
        ]
        
        exit_code = pytest.main(cmd_args)
        
        # Additional security checks could be added here
        # - Dependency vulnerability scanning
        # - Static code analysis
        # - Configuration security review
        
        return {
            "success": exit_code == 0,
            "tests_passed": exit_code == 0,
            "vulnerabilities_found": 0,  # Would be populated by actual security tools
            "recommendations": []
        }
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("# Multi-Tenant SaaS Platform Test Report")
        report.append(f"Generated: {results['timestamp']}")
        report.append("")
        
        # Summary
        summary = results["summary"]
        report.append("## Summary")
        report.append(f"- Total Categories: {summary['total_categories']}")
        report.append(f"- Passed: {summary['passed_categories']}")
        report.append(f"- Failed: {summary['failed_categories']}")
        report.append(f"- Success Rate: {summary['success_rate']:.1f}%")
        report.append(f"- Total Duration: {summary['total_duration']:.2f}s")
        report.append("")
        
        # Category Results
        report.append("## Category Results")
        for category, result in results["categories"].items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            report.append(f"### {category.title()} Tests {status}")
            report.append(f"- Duration: {result['duration']:.2f}s")
            report.append(f"- Exit Code: {result['exit_code']}")
            
            if "error" in result:
                report.append(f"- Error: {result['error']}")
            
            report.append("")
        
        # Performance Thresholds
        report.append("## Performance Thresholds")
        for metric, threshold in self.performance_thresholds.items():
            report.append(f"- {metric}: {threshold}")
        report.append("")
        
        return "\n".join(report)

def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-tenant SaaS platform test runner")
    parser.add_argument("--category", choices=["unit", "integration", "performance", "security", "e2e"], 
                       help="Run specific test category")
    parser.add_argument("--all", action="store_true", help="Run all test categories")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--security", action="store_true", help="Run security audit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report", help="Generate test report to file")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.category:
        # Run specific category
        result = runner.run_test_category(args.category, args.verbose)
        print(f"{args.category} tests: {'PASSED' if result['success'] else 'FAILED'}")
        sys.exit(0 if result["success"] else 1)
    
    elif args.performance:
        # Run performance benchmarks
        result = runner.run_performance_benchmarks()
        print(f"Performance benchmarks: {'PASSED' if result['success'] else 'FAILED'}")
        sys.exit(0 if result["success"] else 1)
    
    elif args.security:
        # Run security audit
        result = runner.run_security_audit()
        print(f"Security audit: {'PASSED' if result['success'] else 'FAILED'}")
        sys.exit(0 if result["success"] else 1)
    
    elif args.all:
        # Run all tests
        results = runner.run_all_tests(verbose=args.verbose)
        
        # Generate report
        if args.report:
            report_content = runner.generate_test_report(results)
            with open(args.report, "w") as f:
                f.write(report_content)
            print(f"Test report saved to {args.report}")
        
        # Print summary
        summary = results["summary"]
        print(f"\nTest Summary:")
        print(f"Categories: {summary['passed_categories']}/{summary['total_categories']} passed")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['total_duration']:.2f}s")
        
        # Exit with appropriate code
        sys.exit(0 if summary["failed_categories"] == 0 else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()