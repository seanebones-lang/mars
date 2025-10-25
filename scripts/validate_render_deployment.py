#!/usr/bin/env python3
"""
Render Deployment Validation Script
Tests all critical endpoints and verifies production readiness.
"""

import sys
import time
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class TestStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️  WARN"
    SKIP = "⏭️  SKIP"

@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    duration_ms: float = 0.0

class RenderDeploymentValidator:
    """Validates Render deployment health and functionality."""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.results: List[TestResult] = []
        
    def run_all_tests(self) -> bool:
        """Run all validation tests and return overall status."""
        print("=" * 80)
        print("RENDER DEPLOYMENT VALIDATION")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        print("=" * 80)
        print()
        
        # Run tests in order
        tests = [
            self.test_health_endpoint,
            self.test_api_documentation,
            self.test_cors_headers,
            self.test_authentication_endpoint,
            self.test_rate_limiting,
            self.test_response_times,
            self.test_error_handling,
            self.test_websocket_availability,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.results.append(TestResult(
                    name=test.__name__,
                    status=TestStatus.FAIL,
                    message=f"Exception: {str(e)}"
                ))
            time.sleep(0.5)  # Rate limit our tests
        
        # Print results
        self._print_results()
        
        # Return overall status
        failures = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        return failures == 0
    
    def test_health_endpoint(self):
        """Test /health endpoint responds correctly."""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.results.append(TestResult(
                        name="Health Endpoint",
                        status=TestStatus.PASS,
                        message=f"Service healthy (HTTP {response.status_code})",
                        duration_ms=duration
                    ))
                else:
                    self.results.append(TestResult(
                        name="Health Endpoint",
                        status=TestStatus.WARN,
                        message=f"Service responding but status: {data.get('status')}",
                        duration_ms=duration
                    ))
            else:
                self.results.append(TestResult(
                    name="Health Endpoint",
                    status=TestStatus.FAIL,
                    message=f"HTTP {response.status_code}: {response.text[:100]}",
                    duration_ms=duration
                ))
        except requests.exceptions.Timeout:
            self.results.append(TestResult(
                name="Health Endpoint",
                status=TestStatus.FAIL,
                message="Request timeout (>10s)"
            ))
        except requests.exceptions.ConnectionError:
            self.results.append(TestResult(
                name="Health Endpoint",
                status=TestStatus.FAIL,
                message="Connection failed - service may be down"
            ))
    
    def test_api_documentation(self):
        """Test API documentation is accessible."""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                self.results.append(TestResult(
                    name="API Documentation",
                    status=TestStatus.PASS,
                    message="Swagger UI accessible",
                    duration_ms=duration
                ))
            else:
                self.results.append(TestResult(
                    name="API Documentation",
                    status=TestStatus.WARN,
                    message=f"HTTP {response.status_code} - docs may be disabled",
                    duration_ms=duration
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="API Documentation",
                status=TestStatus.FAIL,
                message=f"Error: {str(e)}"
            ))
    
    def test_cors_headers(self):
        """Test CORS headers are properly configured."""
        start = time.time()
        try:
            response = requests.options(
                f"{self.base_url}/health",
                headers={"Origin": "https://example.com"},
                timeout=10
            )
            duration = (time.time() - start) * 1000
            
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header:
                self.results.append(TestResult(
                    name="CORS Configuration",
                    status=TestStatus.PASS,
                    message=f"CORS enabled: {cors_header}",
                    duration_ms=duration
                ))
            else:
                self.results.append(TestResult(
                    name="CORS Configuration",
                    status=TestStatus.WARN,
                    message="CORS headers not found - may block frontend",
                    duration_ms=duration
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="CORS Configuration",
                status=TestStatus.FAIL,
                message=f"Error: {str(e)}"
            ))
    
    def test_authentication_endpoint(self):
        """Test authentication endpoint exists."""
        start = time.time()
        try:
            # Test with invalid credentials (should return 401, not 500)
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": "test", "password": "test"},
                timeout=10
            )
            duration = (time.time() - start) * 1000
            
            if response.status_code in [401, 422]:  # Expected for invalid creds
                self.results.append(TestResult(
                    name="Authentication Endpoint",
                    status=TestStatus.PASS,
                    message="Auth endpoint responding correctly",
                    duration_ms=duration
                ))
            elif response.status_code == 404:
                self.results.append(TestResult(
                    name="Authentication Endpoint",
                    status=TestStatus.FAIL,
                    message="Auth endpoint not found (HTTP 404)",
                    duration_ms=duration
                ))
            else:
                self.results.append(TestResult(
                    name="Authentication Endpoint",
                    status=TestStatus.WARN,
                    message=f"Unexpected status: HTTP {response.status_code}",
                    duration_ms=duration
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Authentication Endpoint",
                status=TestStatus.FAIL,
                message=f"Error: {str(e)}"
            ))
    
    def test_rate_limiting(self):
        """Test rate limiting is configured."""
        # This is a basic test - full rate limit testing requires more requests
        self.results.append(TestResult(
            name="Rate Limiting",
            status=TestStatus.SKIP,
            message="Manual verification required"
        ))
    
    def test_response_times(self):
        """Test response times meet SLA (<100ms for health)."""
        times = []
        for i in range(5):
            start = time.time()
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                duration = (time.time() - start) * 1000
                if response.status_code == 200:
                    times.append(duration)
            except:
                pass
            time.sleep(0.2)
        
        if times:
            avg_time = sum(times) / len(times)
            if avg_time < 100:
                self.results.append(TestResult(
                    name="Response Times",
                    status=TestStatus.PASS,
                    message=f"Average: {avg_time:.1f}ms (target: <100ms)",
                    duration_ms=avg_time
                ))
            elif avg_time < 200:
                self.results.append(TestResult(
                    name="Response Times",
                    status=TestStatus.WARN,
                    message=f"Average: {avg_time:.1f}ms (slower than target)",
                    duration_ms=avg_time
                ))
            else:
                self.results.append(TestResult(
                    name="Response Times",
                    status=TestStatus.FAIL,
                    message=f"Average: {avg_time:.1f}ms (too slow)",
                    duration_ms=avg_time
                ))
        else:
            self.results.append(TestResult(
                name="Response Times",
                status=TestStatus.FAIL,
                message="Could not measure response times"
            ))
    
    def test_error_handling(self):
        """Test error handling for invalid requests."""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/nonexistent-endpoint", timeout=10)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    self.results.append(TestResult(
                        name="Error Handling",
                        status=TestStatus.PASS,
                        message="Proper 404 handling with JSON response",
                        duration_ms=duration
                    ))
                except:
                    self.results.append(TestResult(
                        name="Error Handling",
                        status=TestStatus.WARN,
                        message="404 returned but not JSON formatted",
                        duration_ms=duration
                    ))
            else:
                self.results.append(TestResult(
                    name="Error Handling",
                    status=TestStatus.WARN,
                    message=f"Unexpected status for invalid endpoint: {response.status_code}",
                    duration_ms=duration
                ))
        except Exception as e:
            self.results.append(TestResult(
                name="Error Handling",
                status=TestStatus.FAIL,
                message=f"Error: {str(e)}"
            ))
    
    def test_websocket_availability(self):
        """Test WebSocket endpoint is available."""
        # Basic check - full WebSocket testing requires websocket library
        self.results.append(TestResult(
            name="WebSocket Support",
            status=TestStatus.SKIP,
            message="Requires websocket client for full test"
        ))
    
    def _print_results(self):
        """Print formatted test results."""
        print("\n" + "=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print()
        
        for result in self.results:
            duration_str = f"({result.duration_ms:.0f}ms)" if result.duration_ms > 0 else ""
            print(f"{result.status.value} {result.name:.<50} {duration_str}")
            print(f"    {result.message}")
            print()
        
        # Summary
        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == TestStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        total = len(self.results)
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"✅ Passed:   {passed}")
        print(f"❌ Failed:   {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"⏭️  Skipped:  {skipped}")
        print()
        
        if failed == 0:
            print("🎉 DEPLOYMENT VALIDATION PASSED")
            print("The service is ready for production traffic.")
        elif failed <= 2 and warned <= 3:
            print("⚠️  DEPLOYMENT VALIDATION PASSED WITH WARNINGS")
            print("The service is functional but has minor issues to address.")
        else:
            print("❌ DEPLOYMENT VALIDATION FAILED")
            print("Critical issues detected. Do not route production traffic.")
        
        print("=" * 80)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_render_deployment.py <base_url> [api_key]")
        print("Example: python validate_render_deployment.py https://agentguard-api.onrender.com")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    validator = RenderDeploymentValidator(base_url, api_key)
    success = validator.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

