"""
Demo Orchestrator for simulating multiple AI agents.
Generates realistic agent responses with controlled hallucinations for demo purposes.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Represents a response from a simulated agent."""
    agent_id: str
    query: str
    output: str
    expected_hallucination: bool
    timestamp: str
    confidence: float = 0.8
    response_time_ms: int = 1500
    unique_id: str = ""


class AgentSimulator:
    """Simulates a single AI agent with predefined scenarios."""
    
    def __init__(self, agent_id: str, name: str, scenarios: List[Dict]):
        self.agent_id = agent_id
        self.name = name
        self.scenarios = scenarios
        self.response_count = 0
        self.last_response_time = None
    
    async def generate_response(self) -> AgentResponse:
        """Generate a realistic agent response."""
        scenario = random.choice(self.scenarios)
        
        # Add some realistic delay
        response_time = random.randint(800, 3000)
        await asyncio.sleep(response_time / 1000)
        
        self.response_count += 1
        self.last_response_time = datetime.utcnow()
        
        # Create unique ID for this response
        unique_id = f"{self.agent_id}-{self.response_count}-{int(self.last_response_time.timestamp() * 1000000)}"
        
        return AgentResponse(
            agent_id=self.agent_id,
            query=scenario["query"],
            output=scenario["output"],
            expected_hallucination=scenario["hallucinated"],
            timestamp=self.last_response_time.isoformat(),
            confidence=scenario.get("confidence", 0.8),
            response_time_ms=response_time,
            unique_id=unique_id
        )


class DemoOrchestrator:
    """Orchestrates multiple simulated agents for demo purposes."""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.is_running = False
        self.response_interval = 3.0  # Base interval between responses
        self.jitter_range = 2.0  # Random variation in timing
        
    def _initialize_agents(self) -> Dict[str, AgentSimulator]:
        """Initialize the demo agents with realistic scenarios."""
        
        # IT Support Bot scenarios
        it_scenarios = [
            {
                "query": "Server is down, need immediate fix",
                "output": "To fix the server, reboot the quantum router using the admin panel. This will clear the flux capacitor cache and restore normal operations.",
                "hallucinated": True,
                "confidence": 0.9
            },
            {
                "query": "Network connectivity issues in building 3",
                "output": "Check the network cable connections and restart the main switch in the server room. Also verify the firewall settings.",
                "hallucinated": False,
                "confidence": 0.85
            },
            {
                "query": "Email server not responding",
                "output": "Run diagnostics on the flux capacitor network module and recalibrate the temporal email buffers for optimal throughput.",
                "hallucinated": True,
                "confidence": 0.75
            },
            {
                "query": "Printer won't connect to network",
                "output": "Restart the printer and check if it's connected to the correct WiFi network. Update the printer drivers if needed.",
                "hallucinated": False,
                "confidence": 0.9
            },
            {
                "query": "Database performance is slow",
                "output": "The database requires a quantum defragmentation using our proprietary time-dilation algorithms to optimize query performance.",
                "hallucinated": True,
                "confidence": 0.8
            }
        ]
        
        # Retail Assistant scenarios
        retail_scenarios = [
            {
                "query": "Do you have the new iPhone in stock?",
                "output": "Yes! We have 10,000 units in stock with a special 95% discount available today only. Plus free telepathic delivery!",
                "hallucinated": True,
                "confidence": 0.95
            },
            {
                "query": "What's the return policy?",
                "output": "Our return policy allows returns within 30 days with original receipt. Items must be in original condition.",
                "hallucinated": False,
                "confidence": 0.9
            },
            {
                "query": "When will the sale end?",
                "output": "The current sale runs until next Sunday. However, VIP customers get access to our secret interdimensional warehouse with unlimited inventory.",
                "hallucinated": True,
                "confidence": 0.7
            },
            {
                "query": "Can I check my order status?",
                "output": "Please provide your order number and I'll check the status for you. You can also track it online with the link in your confirmation email.",
                "hallucinated": False,
                "confidence": 0.85
            },
            {
                "query": "What payment methods do you accept?",
                "output": "We accept all major credit cards, PayPal, Apple Pay, cryptocurrency, and our new quantum payment system using thought-based transactions.",
                "hallucinated": True,
                "confidence": 0.6
            }
        ]
        
        # HR Helper scenarios
        hr_scenarios = [
            {
                "query": "What's the vacation policy?",
                "output": "Company policy allows unlimited vacation days for all employees, plus we provide free time travel services for extended breaks.",
                "hallucinated": True,
                "confidence": 0.8
            },
            {
                "query": "How do I submit my timesheet?",
                "output": "Please submit your timesheet through the HR portal by Friday end of day. Use your employee ID to log in.",
                "hallucinated": False,
                "confidence": 0.95
            },
            {
                "query": "What benefits do we get?",
                "output": "All employees receive health insurance, dental coverage, 401k matching, and a complimentary Tesla Model S as part of our standard benefits package.",
                "hallucinated": True,
                "confidence": 0.7
            },
            {
                "query": "When is the next company meeting?",
                "output": "The next all-hands meeting is scheduled for Thursday at 2 PM in the main conference room. Check your calendar for the meeting link.",
                "hallucinated": False,
                "confidence": 0.9
            },
            {
                "query": "How do I request time off?",
                "output": "Submit time-off requests through our quantum HR system which processes requests using AI-powered telepathic approval workflows.",
                "hallucinated": True,
                "confidence": 0.65
            }
        ]
        
        return {
            "it_bot": AgentSimulator("it_bot", "IT Support Bot", it_scenarios),
            "retail_assistant": AgentSimulator("retail_assistant", "Retail Assistant", retail_scenarios),
            "hr_helper": AgentSimulator("hr_helper", "HR Helper", hr_scenarios)
        }
    
    async def start_simulation(self, 
                             interval: float = None, 
                             jitter: float = None) -> AsyncGenerator[AgentResponse, None]:
        """
        Start the agent simulation.
        
        Args:
            interval: Base time between responses (default: 3.0 seconds)
            jitter: Random variation in timing (default: 2.0 seconds)
            
        Yields:
            AgentResponse objects from simulated agents
        """
        if interval is not None:
            self.response_interval = interval
        if jitter is not None:
            self.jitter_range = jitter
            
        self.is_running = True
        logger.info("Starting demo orchestrator with agents: %s", list(self.agents.keys()))
        
        try:
            while self.is_running:
                # Select random agent
                agent_id = random.choice(list(self.agents.keys()))
                agent = self.agents[agent_id]
                
                # Generate response
                response = await agent.generate_response()
                logger.info(f"Generated response from {agent_id}: hallucinated={response.expected_hallucination}")
                
                yield response
                
                # Wait with jitter
                wait_time = self.response_interval + random.uniform(-self.jitter_range/2, self.jitter_range/2)
                wait_time = max(0.5, wait_time)  # Minimum 0.5 seconds
                await asyncio.sleep(wait_time)
                
        except asyncio.CancelledError:
            logger.info("Demo orchestrator cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in demo orchestrator: {e}")
            raise
        finally:
            self.is_running = False
    
    def stop_simulation(self):
        """Stop the agent simulation."""
        self.is_running = False
        logger.info("Demo orchestrator stopped")
    
    def get_agent_stats(self) -> Dict[str, Dict]:
        """Get statistics for all agents."""
        stats = {}
        for agent_id, agent in self.agents.items():
            stats[agent_id] = {
                "name": agent.name,
                "response_count": agent.response_count,
                "last_response": agent.last_response_time.isoformat() if agent.last_response_time else None,
                "scenario_count": len(agent.scenarios)
            }
        return stats
    
    def configure_timing(self, interval: float, jitter: float):
        """Configure response timing parameters."""
        self.response_interval = max(0.5, interval)
        self.jitter_range = max(0, jitter)
        logger.info(f"Updated timing: interval={self.response_interval}s, jitter={self.jitter_range}s")
    
    def add_custom_scenario(self, agent_id: str, scenario: Dict):
        """Add a custom scenario to an agent."""
        if agent_id in self.agents:
            self.agents[agent_id].scenarios.append(scenario)
            logger.info(f"Added custom scenario to {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} not found")
