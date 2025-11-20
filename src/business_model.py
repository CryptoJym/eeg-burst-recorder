"""
Business Model Canvas & Unit Economics Calculator
Agent 30: Business Strategy & Modeling

This module provides tools for generating a Business Model Canvas and calculating
key unit economics for the Symbiosis platform.

Author: Agent 30 - Business Strategist
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from datetime import datetime


@dataclass
class UnitEconomics:
    """Data class for unit economics inputs and outputs."""
    # Inputs
    monthly_price: float
    cac: float  # Customer Acquisition Cost
    monthly_churn_rate: float  # 0.0 to 1.0
    active_users: int
    
    # Outputs (Calculated)
    ltv: float = 0.0  # Lifetime Value
    mrr: float = 0.0  # Monthly Recurring Revenue
    ltv_cac_ratio: float = 0.0
    payback_period_months: float = 0.0


class BusinessModelCanvas:
    """
    Business Model Canvas generator and validator.
    """
    
    def __init__(self):
        """Initialize empty canvas."""
        self.blocks = {
            "key_partners": [],
            "key_activities": [],
            "key_resources": [],
            "value_propositions": [],
            "customer_relationships": [],
            "channels": [],
            "customer_segments": [],
            "cost_structure": [],
            "revenue_streams": []
        }
        self.metadata = {
            "project": "Symbiosis",
            "version": "1.0",
            "updated_at": datetime.now().isoformat()
        }

    def update_block(self, block_name: str, items: List[str]):
        """
        Update a specific block of the canvas.
        
        Args:
            block_name: Name of the canvas block (snake_case)
            items: List of items to add
        """
        if block_name not in self.blocks:
            raise ValueError(f"Invalid block name: {block_name}")
        
        self.blocks[block_name] = items
        self.metadata["updated_at"] = datetime.now().isoformat()

    def get_block(self, block_name: str) -> List[str]:
        """Get items for a block."""
        return self.blocks.get(block_name, [])

    def validate(self) -> Dict[str, Any]:
        """
        Validate that the canvas is complete.
        
        Returns:
            Dict with 'is_complete' (bool) and 'missing_blocks' (list)
        """
        missing = [k for k, v in self.blocks.items() if not v]
        return {
            "is_complete": len(missing) == 0,
            "missing_blocks": missing
        }

    def calculate_economics(
        self, 
        monthly_price: float, 
        cac: float, 
        monthly_churn_rate: float,
        active_users: int
    ) -> UnitEconomics:
        """
        Calculate unit economics based on inputs.
        
        Args:
            monthly_price: Price per month per user
            cac: Cost to acquire one customer
            monthly_churn_rate: Monthly churn (e.g., 0.05 for 5%)
            active_users: Number of current active users
            
        Returns:
            UnitEconomics object with calculated metrics
        """
        if monthly_churn_rate <= 0 or monthly_churn_rate >= 1:
            raise ValueError("Churn rate must be between 0 and 1 (exclusive of 0)")
            
        # Lifetime Value = (ARPU / Churn)
        # Note: This is a simplified LTV model (LTV = Margin / Churn) assuming 100% margin for software
        ltv = monthly_price / monthly_churn_rate
        
        # MRR
        mrr = monthly_price * active_users
        
        # LTV:CAC Ratio
        ratio = ltv / cac if cac > 0 else 0.0
        
        # Payback Period = CAC / ARPU
        payback = cac / monthly_price if monthly_price > 0 else 0.0
        
        return UnitEconomics(
            monthly_price=monthly_price,
            cac=cac,
            monthly_churn_rate=monthly_churn_rate,
            active_users=active_users,
            ltv=round(ltv, 2),
            mrr=round(mrr, 2),
            ltv_cac_ratio=round(ratio, 2),
            payback_period_months=round(payback, 1)
        )

    def generate_markdown_report(self) -> str:
        """Generate a Markdown representation of the canvas."""
        md = [f"# Business Model Canvas: {self.metadata['project']}", 
              f"**Version**: {self.metadata['version']}",
              f"**Date**: {self.metadata['updated_at']}",
              "\n---",
              ""]
        
        # Layout logic (simplified for markdown list)
        layout_order = [
            ("Value Propositions", "value_propositions"),
            ("Customer Segments", "customer_segments"),
            ("Channels", "channels"),
            ("Customer Relationships", "customer_relationships"),
            ("Revenue Streams", "revenue_streams"),
            ("Key Resources", "key_resources"),
            ("Key Activities", "key_activities"),
            ("Key Partners", "key_partners"),
            ("Cost Structure", "cost_structure")
        ]
        
        for title, key in layout_order:
            md.append(f"## {title}")
            items = self.blocks[key]
            if not items:
                md.append("* *Empty*")
            else:
                for item in items:
                    md.append(f"- {item}")
            md.append("")
            
        return "\n".join(md)

    def to_json(self) -> str:
        """Export canvas to JSON string."""
        return json.dumps({
            "metadata": self.metadata,
            "blocks": self.blocks
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'BusinessModelCanvas':
        """Create canvas from JSON string."""
        data = json.loads(json_str)
        canvas = cls()
        canvas.blocks = data.get("blocks", canvas.blocks)
        canvas.metadata = data.get("metadata", canvas.metadata)
        return canvas
