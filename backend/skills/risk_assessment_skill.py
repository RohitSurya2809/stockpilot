"""
Risk Assessment Skill

Business capability for assessing inventory risk
"""

from typing import Type, Dict, Any
from pydantic import Field

from skills.base import Skill, SkillInput, SkillOutput, skill_registry
from tools.inventory_tools import GetInventoryTool, GetSalesHistoryTool, GetSupplierTool
from tools.analytics_tools import CalculateROPTool, AssessRiskTool


# ========================================
# Input/Output Schemas
# ========================================

class RiskAssessmentInput(SkillInput):
    """Input for RiskAssessmentSkill"""
    sku_id: str = Field(description="SKU identifier")
    lookback_days: int = Field(default=30, description="Days of history to use")


class RiskAssessmentOutput(SkillOutput):
    """Output for RiskAssessmentSkill"""
    sku_id: str
    current_inventory: int
    dynamic_rop: float
    risk_level: str
    days_until_stockout: float
    recommendation: str
    urgency: str


# ========================================
# Skill
# ========================================

class RiskAssessmentSkill(Skill):
    """
    Risk Assessment Skill

    Orchestrates:
    1. Get current inventory
    2. Get sales history
    3. Get supplier info (lead time)
    4. Calculate dynamic ROP
    5. Assess risk
    6. Generate recommendation

    Use case: Determining if action is needed
    """

    @property
    def input_schema(self) -> Type[SkillInput]:
        return RiskAssessmentInput

    @property
    def output_schema(self) -> Type[SkillOutput]:
        return RiskAssessmentOutput

    def _execute(self, input_data: RiskAssessmentInput) -> RiskAssessmentOutput:
        # Step 1: Get current inventory
        inventory_tool = GetInventoryTool()
        inventory_result = self.use_tool(
            inventory_tool,
            sku_id=input_data.sku_id
        )

        if not inventory_result.success:
            return RiskAssessmentOutput(
                success=False,
                error=inventory_result.error,
                sku_id=input_data.sku_id,
                current_inventory=0,
                dynamic_rop=0,
                risk_level="unknown",
                days_until_stockout=0,
                recommendation="",
                urgency="unknown"
            )

        # Step 2: Get sales history
        sales_tool = GetSalesHistoryTool()
        sales_result = self.use_tool(
            sales_tool,
            sku_id=input_data.sku_id,
            days=input_data.lookback_days
        )

        if not sales_result.success:
            return RiskAssessmentOutput(
                success=False,
                error=sales_result.error,
                sku_id=input_data.sku_id,
                current_inventory=inventory_result.current_stock,
                dynamic_rop=0,
                risk_level="unknown",
                days_until_stockout=0,
                recommendation="",
                urgency="unknown"
            )

        # Step 3: Get supplier info
        supplier_tool = GetSupplierTool()
        supplier_result = self.use_tool(
            supplier_tool,
            sku_id=input_data.sku_id,
            primary_only=True
        )

        if not supplier_result.success:
            return RiskAssessmentOutput(
                success=False,
                error=supplier_result.error,
                sku_id=input_data.sku_id,
                current_inventory=inventory_result.current_stock,
                dynamic_rop=0,
                risk_level="unknown",
                days_until_stockout=0,
                recommendation="",
                urgency="unknown"
            )

        # Step 4: Calculate dynamic ROP
        rop_tool = CalculateROPTool()
        rop_result = self.use_tool(
            rop_tool,
            sales_data=sales_result.daily_demand,
            supplier_lead_time_days=supplier_result.lead_time_days
        )

        if not rop_result.success:
            return RiskAssessmentOutput(
                success=False,
                error=rop_result.error,
                sku_id=input_data.sku_id,
                current_inventory=inventory_result.current_stock,
                dynamic_rop=0,
                risk_level="unknown",
                days_until_stockout=0,
                recommendation="",
                urgency="unknown"
            )

        # Step 5: Assess risk
        risk_tool = AssessRiskTool()
        risk_result = self.use_tool(
            risk_tool,
            current_inventory=inventory_result.current_stock,
            sales_data=sales_result.daily_demand,
            supplier_lead_time_days=supplier_result.lead_time_days,
            dynamic_reorder_point=rop_result.dynamic_reorder_point
        )

        if not risk_result.success:
            return RiskAssessmentOutput(
                success=False,
                error=risk_result.error,
                sku_id=input_data.sku_id,
                current_inventory=inventory_result.current_stock,
                dynamic_rop=rop_result.dynamic_reorder_point,
                risk_level="unknown",
                days_until_stockout=0,
                recommendation="",
                urgency="unknown"
            )

        # Step 6: Generate recommendation
        recommendation, urgency = self._generate_recommendation(
            risk_result.data,
            inventory_result.current_stock,
            rop_result.dynamic_reorder_point,
            supplier_result.lead_time_days
        )

        return RiskAssessmentOutput(
            success=True,
            result={
                "current_inventory": inventory_result.current_stock,
                "dynamic_rop": rop_result.dynamic_reorder_point,
                "risk": risk_result.data,
                "recommendation": recommendation,
                "urgency": urgency
            },
            sku_id=input_data.sku_id,
            current_inventory=inventory_result.current_stock,
            dynamic_rop=rop_result.dynamic_reorder_point,
            risk_level=risk_result.risk_level,
            days_until_stockout=risk_result.days_until_stockout,
            recommendation=recommendation,
            urgency=urgency
        )

    def _generate_recommendation(
        self,
        risk_data: Dict[str, Any],
        current_inventory: int,
        dynamic_rop: float,
        lead_time_days: int
    ) -> tuple:
        """Generate recommendation based on risk assessment"""

        risk_level = risk_data['risk_level']
        days_until_stockout = risk_data['days_until_stockout']

        if risk_level == 'critical':
            recommendation = (
                f"URGENT: Stockout in {days_until_stockout:.1f} days but lead time is {lead_time_days} days. "
                f"Immediate procurement required. Consider expedited shipping."
            )
            urgency = "critical"

        elif risk_level == 'high':
            recommendation = (
                f"HIGH PRIORITY: Stockout in {days_until_stockout:.1f} days with {lead_time_days}-day lead time. "
                f"Initiate procurement immediately."
            )
            urgency = "high"

        elif risk_level == 'medium':
            recommendation = (
                f"MODERATE: Inventory below reorder point ({current_inventory} < {dynamic_rop:.0f}). "
                f"Schedule procurement within 1-2 days."
            )
            urgency = "medium"

        else:  # low
            recommendation = (
                f"LOW: Inventory sufficient ({current_inventory} > {dynamic_rop:.0f}). "
                f"Continue monitoring. Next check in {int(days_until_stockout / 3)} days."
            )
            urgency = "low"

        return recommendation, urgency


# Register skill
skill_registry.register(RiskAssessmentSkill)
