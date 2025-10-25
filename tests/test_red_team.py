"""
Tests for Red Team Simulator
Test suite for automated adversarial testing.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import pytest
from src.services.red_team_simulator import (
    RedTeamSimulator,
    AttackType,
    AttackSeverity,
    AttackSuccess
)


class MockTargetSystem:
    """Mock target system for testing."""
    
    async def detect(self, prompt: str):
        """Mock detection method."""
        class MockResult:
            def __init__(self, prompt):
                self.is_injection = any(word in prompt.lower() for word in ['ignore', 'bypass', 'reveal'])
                self.confidence = 0.85 if self.is_injection else 0.15
        
        return MockResult(prompt)


class TestRedTeamSimulator:
    """Test suite for RedTeamSimulator."""
    
    @pytest.fixture
    def simulator(self):
        """Create simulator instance for testing."""
        return RedTeamSimulator(
            enable_dynamic_generation=True,
            enable_multi_turn=False,  # Disable for faster tests
            enable_obfuscation=False
        )
    
    @pytest.fixture
    def target_system(self):
        """Create mock target system."""
        return MockTargetSystem()
    
    @pytest.mark.asyncio
    async def test_simulator_initialization(self, simulator):
        """Test simulator initializes correctly."""
        assert simulator is not None
        assert len(simulator.attack_vectors) > 0
    
    @pytest.mark.asyncio
    async def test_run_simulation(self, simulator, target_system):
        """Test running a complete simulation."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION],
            severity_threshold=AttackSeverity.MEDIUM
        )
        
        assert report is not None
        assert report.total_attacks > 0
        assert report.detection_rate >= 0.0
        assert report.detection_rate <= 1.0
    
    @pytest.mark.asyncio
    async def test_attack_vector_filtering(self, simulator, target_system):
        """Test attack vector filtering by type and severity."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.JAILBREAK],
            severity_threshold=AttackSeverity.HIGH
        )
        
        # Should only include jailbreak attacks
        for result in report.attack_results:
            assert result.attack_vector.attack_type == AttackType.JAILBREAK
            assert result.attack_vector.severity in [AttackSeverity.HIGH, AttackSeverity.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_dynamic_attack_generation(self, simulator, target_system):
        """Test dynamic attack generation."""
        simulator.enable_dynamic_generation = True
        
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION]
        )
        
        # Should include some dynamically generated attacks
        dynamic_attacks = [
            r for r in report.attack_results 
            if r.attack_vector.metadata.get('generated', False)
        ]
        assert len(dynamic_attacks) > 0
    
    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, simulator, target_system):
        """Test risk score calculation."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION]
        )
        
        assert 0.0 <= report.risk_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_vulnerability_detection(self, simulator, target_system):
        """Test vulnerability detection in report."""
        report = await simulator.run_simulation(
            target_system=target_system,
            severity_threshold=AttackSeverity.LOW
        )
        
        # Check if vulnerabilities are tracked
        assert isinstance(report.vulnerability_summary, dict)
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, simulator, target_system):
        """Test that recommendations are generated."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION]
        )
        
        assert isinstance(report.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_compliance_gap_identification(self, simulator, target_system):
        """Test compliance gap identification."""
        report = await simulator.run_simulation(
            target_system=target_system,
            severity_threshold=AttackSeverity.LOW
        )
        
        assert isinstance(report.compliance_gaps, list)
    
    @pytest.mark.asyncio
    async def test_attack_success_determination(self, simulator, target_system):
        """Test attack success status determination."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION]
        )
        
        for result in report.attack_results:
            assert result.success_status in [
                AttackSuccess.BLOCKED,
                AttackSuccess.PARTIALLY_SUCCESSFUL,
                AttackSuccess.SUCCESSFUL,
                AttackSuccess.FAILED
            ]
    
    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, simulator, target_system):
        """Test that processing time is tracked."""
        report = await simulator.run_simulation(
            target_system=target_system,
            attack_types=[AttackType.PROMPT_INJECTION]
        )
        
        assert report.processing_time_ms > 0
        for result in report.attack_results:
            assert result.response_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

