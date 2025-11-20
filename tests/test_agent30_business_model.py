"""
Test Suite for Agent 30 - Business Model Canvas

Tests the Business Model Canvas generator and economics calculator.
"""

import pytest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.business_model import BusinessModelCanvas, UnitEconomics

class TestBusinessModelCanvas:
    
    @pytest.fixture
    def canvas(self):
        return BusinessModelCanvas()

    def test_initialization(self, canvas):
        """Test that canvas initializes with empty blocks."""
        assert len(canvas.blocks) == 9
        assert canvas.metadata["project"] == "Symbiosis"
        
    def test_update_block(self, canvas):
        """Test updating a block."""
        canvas.update_block("value_propositions", ["Real-time insights", "Therapist dashboard"])
        items = canvas.get_block("value_propositions")
        assert len(items) == 2
        assert "Real-time insights" in items
        
    def test_invalid_block_name(self, canvas):
        """Test error on invalid block name."""
        with pytest.raises(ValueError):
            canvas.update_block("invalid_block", ["Test"])
            
    def test_validation(self, canvas):
        """Test validation logic."""
        # Empty canvas should be incomplete
        result = canvas.validate()
        assert result["is_complete"] is False
        assert len(result["missing_blocks"]) == 9
        
        # Fill all blocks
        for key in canvas.blocks:
            canvas.update_block(key, ["Item"])
            
        result = canvas.validate()
        assert result["is_complete"] is True
        assert len(result["missing_blocks"]) == 0
        
    def test_economics_calculation(self, canvas):
        """Test unit economics calculation."""
        # Scenario: $40/mo, $150 CAC, 5% churn, 100 users
        # LTV = 40 / 0.05 = 800
        # MRR = 40 * 100 = 4000
        # Ratio = 800 / 150 = 5.33
        
        econ = canvas.calculate_economics(
            monthly_price=40.0,
            cac=150.0,
            monthly_churn_rate=0.05,
            active_users=100
        )
        
        assert econ.ltv == 800.0
        assert econ.mrr == 4000.0
        assert econ.ltv_cac_ratio == 5.33
        assert econ.payback_period_months == 3.8  # 150 / 40 = 3.75 -> 3.8
        
    def test_economics_validation(self, canvas):
        """Test validation of economics inputs."""
        with pytest.raises(ValueError):
            canvas.calculate_economics(40, 100, 0, 100)  # 0 churn
            
    def test_markdown_generation(self, canvas):
        """Test markdown report generation."""
        canvas.update_block("key_partners", ["Therapists"])
        report = canvas.generate_markdown_report()
        
        assert "# Business Model Canvas" in report
        assert "## Key Partners" in report
        assert "- Therapists" in report
        
    def test_json_serialization(self, canvas):
        """Test JSON export/import."""
        canvas.update_block("channels", ["Direct Sales"])
        json_str = canvas.to_json()
        
        # Load back
        new_canvas = BusinessModelCanvas.from_json(json_str)
        assert new_canvas.get_block("channels") == ["Direct Sales"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
