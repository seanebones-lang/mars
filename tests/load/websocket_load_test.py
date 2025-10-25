"""
WebSocket Load Testing for AgentGuard Real-time Monitoring
P0-Critical: Validate WebSocket scalability (10,000+ concurrent connections)

Usage:
    python tests/load/websocket_load_test.py --url wss://agentguard-api.onrender.com/ws/monitor --connections 1000
"""

import asyncio
import websockets
import argparse
import time
import json
from datetime import datetime
from typing import List
import statistics


class WebSocketLoadTester:
    """Load tester for WebSocket connections."""
    
    def __init__(self, url: str, num_connections: int, duration: int = 60):
        """
        Initialize WebSocket load tester.
        
        Args:
            url: WebSocket URL to test
            num_connections: Number of concurrent connections
            duration: Test duration in seconds
        """
        self.url = url
        self.num_connections = num_connections
        self.duration = duration
        
        # Metrics
        self.successful_connections = 0
        self.failed_connections = 0
        self.messages_received = 0
        self.messages_sent = 0
        self.connection_times = []
        self.message_latencies = []
        
        # Control
        self.start_time = None
        self.end_time = None
        self.running = False
    
    async def connect_and_monitor(self, connection_id: int):
        """
        Connect to WebSocket and monitor for duration.
        
        Args:
            connection_id: Unique identifier for this connection
        """
        try:
            connect_start = time.time()
            
            async with websockets.connect(self.url) as websocket:
                connect_time = time.time() - connect_start
                self.connection_times.append(connect_time)
                self.successful_connections += 1
                
                print(f"Connection {connection_id} established in {connect_time:.3f}s")
                
                # Monitor for duration
                end_time = time.time() + self.duration
                
                while time.time() < end_time and self.running:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        
                        self.messages_received += 1
                        
                        # Parse message and calculate latency if timestamp present
                        try:
                            data = json.loads(message)
                            if "timestamp" in data:
                                msg_time = datetime.fromisoformat(data["timestamp"])
                                latency = (datetime.now() - msg_time).total_seconds() * 1000
                                self.message_latencies.append(latency)
                        except (json.JSONDecodeError, ValueError):
                            pass
                        
                    except asyncio.TimeoutError:
                        # No message received, send ping
                        await websocket.ping()
                        self.messages_sent += 1
                    except websockets.exceptions.ConnectionClosed:
                        print(f"Connection {connection_id} closed by server")
                        break
                
        except Exception as e:
            self.failed_connections += 1
            print(f"Connection {connection_id} failed: {e}")
    
    async def run_load_test(self):
        """Run the load test with specified number of connections."""
        print("=" * 80)
        print("AgentGuard WebSocket Load Test")
        print("=" * 80)
        print(f"URL: {self.url}")
        print(f"Connections: {self.num_connections}")
        print(f"Duration: {self.duration}s")
        print("=" * 80)
        
        self.start_time = time.time()
        self.running = True
        
        # Create all connections
        tasks = [
            self.connect_and_monitor(i)
            for i in range(self.num_connections)
        ]
        
        # Run all connections concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = time.time()
        self.running = False
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results and metrics."""
        total_time = self.end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("Load Test Results")
        print("=" * 80)
        
        # Connection metrics
        print("\nConnection Metrics:")
        print(f"  Total Attempted: {self.num_connections}")
        print(f"  Successful: {self.successful_connections}")
        print(f"  Failed: {self.failed_connections}")
        print(f"  Success Rate: {(self.successful_connections / self.num_connections) * 100:.2f}%")
        
        if self.connection_times:
            print(f"\nConnection Time Statistics:")
            print(f"  Average: {statistics.mean(self.connection_times):.3f}s")
            print(f"  Median: {statistics.median(self.connection_times):.3f}s")
            print(f"  Min: {min(self.connection_times):.3f}s")
            print(f"  Max: {max(self.connection_times):.3f}s")
        
        # Message metrics
        print(f"\nMessage Metrics:")
        print(f"  Messages Received: {self.messages_received}")
        print(f"  Messages Sent: {self.messages_sent}")
        print(f"  Messages/sec: {self.messages_received / total_time:.2f}")
        
        if self.message_latencies:
            print(f"\nMessage Latency Statistics:")
            print(f"  Average: {statistics.mean(self.message_latencies):.2f}ms")
            print(f"  Median: {statistics.median(self.message_latencies):.2f}ms")
            print(f"  P95: {statistics.quantiles(self.message_latencies, n=20)[18]:.2f}ms")
            print(f"  Min: {min(self.message_latencies):.2f}ms")
            print(f"  Max: {max(self.message_latencies):.2f}ms")
        
        # Overall metrics
        print(f"\nOverall Metrics:")
        print(f"  Total Duration: {total_time:.2f}s")
        print(f"  Concurrent Connections: {self.successful_connections}")
        
        # Performance validation
        print("\n" + "=" * 80)
        print("Performance Target Validation:")
        success_rate = (self.successful_connections / self.num_connections) * 100
        avg_latency = statistics.mean(self.message_latencies) if self.message_latencies else 0
        
        print(f"✓ Connection Success > 95%: {'PASS' if success_rate > 95 else 'FAIL'} ({success_rate:.2f}%)")
        print(f"✓ Average Latency < 100ms: {'PASS' if avg_latency < 100 else 'FAIL'} ({avg_latency:.2f}ms)")
        print(f"✓ Failed Connections < 5%: {'PASS' if self.failed_connections < self.num_connections * 0.05 else 'FAIL'} ({self.failed_connections})")
        print("=" * 80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="WebSocket Load Testing for AgentGuard")
    parser.add_argument("--url", default="ws://localhost:8000/ws/monitor", help="WebSocket URL")
    parser.add_argument("--connections", type=int, default=100, help="Number of concurrent connections")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    
    args = parser.parse_args()
    
    tester = WebSocketLoadTester(
        url=args.url,
        num_connections=args.connections,
        duration=args.duration
    )
    
    await tester.run_load_test()


if __name__ == "__main__":
    asyncio.run(main())

