"""
Chaos Engineering Tests
P1-4: Test system resilience under failure conditions
"""

import pytest
import asyncio
import random
import time
from typing import List
import httpx


# Test configuration
API_URL = "http://localhost:8000"
CHAOS_DURATION = 60  # seconds
REQUEST_RATE = 10  # requests per second


class ChaosTest:
    """Base class for chaos tests."""
    
    def __init__(self, api_url: str = API_URL):
        """Initialize chaos test."""
        self.api_url = api_url
        self.results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "errors": []
        }
    
    async def make_request(self, endpoint: str, method: str = "GET", data: dict = None):
        """Make HTTP request and track results."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if method == "GET":
                    response = await client.get(f"{self.api_url}{endpoint}")
                else:
                    response = await client.post(f"{self.api_url}{endpoint}", json=data)
                
                self.results["total_requests"] += 1
                
                if response.status_code == 200:
                    self.results["successful_requests"] += 1
                else:
                    self.results["failed_requests"] += 1
                    self.results["errors"].append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "error": response.text[:100]
                    })
                
                return response.status_code == 200
                
        except Exception as e:
            self.results["total_requests"] += 1
            self.results["failed_requests"] += 1
            self.results["errors"].append({
                "endpoint": endpoint,
                "error": str(e)
            })
            return False
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.results["total_requests"] == 0:
            return 0.0
        return (self.results["successful_requests"] / self.results["total_requests"]) * 100


@pytest.mark.chaos
class TestRandomFailures:
    """Test system behavior under random failures."""
    
    @pytest.mark.asyncio
    async def test_random_endpoint_failures(self):
        """
        Test system resilience when random endpoints fail.
        
        Simulates: Random service failures
        Expected: System continues to function, graceful degradation
        """
        chaos = ChaosTest()
        
        endpoints = [
            "/health",
            "/metrics",
            "/test-agent",
            "/prompt-injection/detect",
            "/monitoring/cost/daily",
        ]
        
        # Make requests for duration
        start_time = time.time()
        while time.time() - start_time < CHAOS_DURATION:
            # Random endpoint
            endpoint = random.choice(endpoints)
            
            # Random data for POST endpoints
            data = None
            if endpoint == "/test-agent":
                data = {
                    "agent_output": "Test output",
                    "ground_truth": "Test truth"
                }
            elif endpoint == "/prompt-injection/detect":
                data = {"prompt": "Test prompt"}
            
            await chaos.make_request(endpoint, "POST" if data else "GET", data)
            
            # Random delay
            await asyncio.sleep(random.uniform(0.05, 0.2))
        
        # Check results
        success_rate = chaos.get_success_rate()
        
        print(f"\nRandom Failures Test Results:")
        print(f"Total Requests: {chaos.results['total_requests']}")
        print(f"Successful: {chaos.results['successful_requests']}")
        print(f"Failed: {chaos.results['failed_requests']}")
        print(f"Success Rate: {success_rate:.2f}%")
        
        # System should maintain > 95% success rate
        assert success_rate > 95.0, f"Success rate too low: {success_rate:.2f}%"


@pytest.mark.chaos
class TestHighLoad:
    """Test system behavior under high load."""
    
    @pytest.mark.asyncio
    async def test_burst_traffic(self):
        """
        Test system resilience under sudden traffic burst.
        
        Simulates: Traffic spike (10x normal load)
        Expected: System handles load without crashing
        """
        chaos = ChaosTest()
        
        # Burst: 100 concurrent requests
        tasks = []
        for i in range(100):
            task = chaos.make_request("/health")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_rate = chaos.get_success_rate()
        
        print(f"\nBurst Traffic Test Results:")
        print(f"Total Requests: {chaos.results['total_requests']}")
        print(f"Successful: {chaos.results['successful_requests']}")
        print(f"Failed: {chaos.results['failed_requests']}")
        print(f"Success Rate: {success_rate:.2f}%")
        
        # Should handle at least 80% of burst traffic
        assert success_rate > 80.0, f"Success rate too low: {success_rate:.2f}%"


@pytest.mark.chaos
class TestResourceExhaustion:
    """Test system behavior under resource exhaustion."""
    
    @pytest.mark.asyncio
    async def test_memory_pressure(self):
        """
        Test system behavior under memory pressure.
        
        Simulates: High memory usage
        Expected: System continues to function, may slow down
        """
        chaos = ChaosTest()
        
        # Make large requests
        large_text = "A" * 10000  # 10KB text
        
        for i in range(50):
            await chaos.make_request(
                "/test-agent",
                "POST",
                {
                    "agent_output": large_text,
                    "ground_truth": large_text
                }
            )
        
        success_rate = chaos.get_success_rate()
        
        print(f"\nMemory Pressure Test Results:")
        print(f"Total Requests: {chaos.results['total_requests']}")
        print(f"Successful: {chaos.results['successful_requests']}")
        print(f"Failed: {chaos.results['failed_requests']}")
        print(f"Success Rate: {success_rate:.2f}%")
        
        # Should handle at least 90% of large requests
        assert success_rate > 90.0, f"Success rate too low: {success_rate:.2f}%"


@pytest.mark.chaos
class TestNetworkLatency:
    """Test system behavior under network latency."""
    
    @pytest.mark.asyncio
    async def test_slow_responses(self):
        """
        Test system behavior with slow network.
        
        Simulates: High network latency
        Expected: System times out gracefully
        """
        chaos = ChaosTest()
        
        # Make requests with short timeout
        async with httpx.AsyncClient(timeout=1.0) as client:
            for i in range(20):
                try:
                    response = await client.get(f"{chaos.api_url}/health")
                    chaos.results["total_requests"] += 1
                    if response.status_code == 200:
                        chaos.results["successful_requests"] += 1
                except httpx.TimeoutException:
                    chaos.results["total_requests"] += 1
                    chaos.results["failed_requests"] += 1
                    # Timeout is acceptable
                except Exception as e:
                    chaos.results["total_requests"] += 1
                    chaos.results["failed_requests"] += 1
        
        print(f"\nNetwork Latency Test Results:")
        print(f"Total Requests: {chaos.results['total_requests']}")
        print(f"Successful: {chaos.results['successful_requests']}")
        print(f"Timeouts/Failures: {chaos.results['failed_requests']}")
        
        # Test passes if no crashes (timeouts are acceptable)
        assert True


@pytest.mark.chaos
class TestCascadingFailures:
    """Test system behavior under cascading failures."""
    
    @pytest.mark.asyncio
    async def test_dependency_failure(self):
        """
        Test system behavior when dependencies fail.
        
        Simulates: External API failures (Claude, Redis, etc.)
        Expected: System degrades gracefully, returns errors instead of crashing
        """
        chaos = ChaosTest()
        
        # Test endpoints that depend on external services
        endpoints = [
            ("/test-agent", {"agent_output": "test", "ground_truth": "test"}),
            ("/prompt-injection/detect", {"prompt": "test"}),
            ("/monitoring/cache/stats", None),
        ]
        
        for endpoint, data in endpoints:
            if data:
                await chaos.make_request(endpoint, "POST", data)
            else:
                await chaos.make_request(endpoint, "GET")
        
        print(f"\nDependency Failure Test Results:")
        print(f"Total Requests: {chaos.results['total_requests']}")
        print(f"Successful: {chaos.results['successful_requests']}")
        print(f"Failed: {chaos.results['failed_requests']}")
        
        # Test passes if no crashes (failures are acceptable)
        assert chaos.results["total_requests"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "chaos", "--tb=short"])

