"""
Inventory Agent

Main agent for inventory management decisions
"""

from typing import Type, Dict, Any, Optional
from pydantic import Field

from agents.base import Agent, AgentInput, AgentOutput, AgentDecisionType, agent_registry
from skills.demand_analysis_skill import DemandAnalysisSkill
from skills.risk_assessment_skill import RiskAssessmentSkill


# ========================================
# Input/Output Schemas
# ========================================

class InventoryAgentInput(AgentInput):
    """Input for InventoryAgent"""
    sku_id: str = Field(description="SKU identifier to analyze")
    action: str = Field(default="assess", description="Action to perform: assess, monitor, reorder")


class InventoryAgentOutput(AgentOutput):
    """Output for InventoryAgent"""
    sku_id: str
    demand_insights: Optional[str] = None
    risk_level: Optional[str] = None
    current_inventory: Optional[int] = None
    dynamic_rop: Optional[float] = None
    recommendation: Optional[str] = None


# ========================================
# Agent
# ========================================

class InventoryAgent(Agent):
    """
    Inventory Agent

    Autonomous agent that:
    1. Analyzes demand patterns
    2. Assesses stockout risk
    3. Decides when to reorder
    4. Generates human-readable explanations

    Decision logic:
    - CRITICAL risk -> immediate reorder
    - HIGH risk -> escalate to manager
    - MEDIUM risk -> schedule reorder
    - LOW risk -> continue monitoring
    """

    @property
    def input_schema(self) -> Type[AgentInput]:
        return InventoryAgentInput

    @property
    def output_schema(self) -> Type[AgentOutput]:
        return InventoryAgentOutput

    def _execute(self, input_data: InventoryAgentInput) -> InventoryAgentOutput:
        """
        Execute agent decision-making

        Flow:
        1. Gather intelligence (demand analysis + risk assessment)
        2. Analyze the situation
        3. Make a decision
        4. Generate explanation
        """

        # ========================================
        # Phase 1: Gather Intelligence
        # ========================================

        # Use Demand Analysis Skill
        demand_skill = DemandAnalysisSkill()
        demand_output = self.use_skill(
            demand_skill,
            sku_id=input_data.sku_id,
            lookback_days=30,
            forecast_horizon=30
        )

        if not demand_output.success:
            return InventoryAgentOutput(
                success=False,
                error=f"Demand analysis failed: {demand_output.error}",
                sku_id=input_data.sku_id,
                decision="error",
                decision_type=AgentDecisionType.MONITOR
            )

        self.log_action(f"Analyzed demand for {input_data.sku_id}")

        # Use Risk Assessment Skill
        risk_skill = RiskAssessmentSkill()
        risk_output = self.use_skill(
            risk_skill,
            sku_id=input_data.sku_id,
            lookback_days=30
        )

        if not risk_output.success:
            return InventoryAgentOutput(
                success=False,
                error=f"Risk assessment failed: {risk_output.error}",
                sku_id=input_data.sku_id,
                decision="error",
                decision_type=AgentDecisionType.MONITOR,
                demand_insights=demand_output.insights
            )

        self.log_action(f"Assessed risk for {input_data.sku_id}")

        # ========================================
        # Phase 2: Analyze Situation
        # ========================================

        risk_level = risk_output.risk_level
        urgency = risk_output.urgency
        current_inventory = risk_output.current_inventory
        dynamic_rop = risk_output.dynamic_rop
        days_until_stockout = risk_output.days_until_stockout

        # ========================================
        # Phase 3: Make Decision
        # ========================================

        decision, decision_type, confidence = self._make_decision(
            risk_level=risk_level,
            urgency=urgency,
            current_inventory=current_inventory,
            dynamic_rop=dynamic_rop,
            days_until_stockout=days_until_stockout
        )

        self.log_action(f"Decision: {decision} (confidence: {confidence:.0%})")

        # ========================================
        # Phase 4: Generate Explanation
        # ========================================

        reasoning = self._generate_reasoning(
            sku_id=input_data.sku_id,
            demand_insights=demand_output.insights,
            risk_level=risk_level,
            current_inventory=current_inventory,
            dynamic_rop=dynamic_rop,
            days_until_stockout=days_until_stockout,
            decision=decision,
            urgency=urgency
        )

        return InventoryAgentOutput(
            success=True,
            decision=decision,
            decision_type=decision_type,
            reasoning=reasoning,
            result_data={
                "demand_analysis": demand_output.result,
                "risk_assessment": risk_output.result,
                "decision_details": {
                    "risk_level": risk_level,
                    "urgency": urgency,
                    "confidence": confidence
                }
            },
            confidence_score=confidence,
            sku_id=input_data.sku_id,
            demand_insights=demand_output.insights,
            risk_level=risk_level,
            current_inventory=current_inventory,
            dynamic_rop=dynamic_rop,
            recommendation=risk_output.recommendation
        )

    def _make_decision(
        self,
        risk_level: str,
        urgency: str,
        current_inventory: int,
        dynamic_rop: float,
        days_until_stockout: float
    ) -> tuple:
        """
        Core decision logic

        Returns:
            (decision, decision_type, confidence)
        """

        if risk_level == 'critical':
            # CRITICAL: Immediate action required
            return (
                "IMMEDIATE_REORDER",
                AgentDecisionType.REORDER,
                0.95  # High confidence
            )

        elif risk_level == 'high':
            # HIGH: Escalate to human for approval
            return (
                "ESCALATE_FOR_APPROVAL",
                AgentDecisionType.ESCALATE,
                0.90  # High confidence
            )

        elif risk_level == 'medium':
            # MEDIUM: Schedule reorder
            return (
                "SCHEDULE_REORDER",
                AgentDecisionType.REORDER,
                0.80  # Medium-high confidence
            )

        else:  # low
            # LOW: Continue monitoring
            return (
                "CONTINUE_MONITORING",
                AgentDecisionType.MONITOR,
                0.70  # Medium confidence
            )

    def _generate_reasoning(
        self,
        sku_id: str,
        demand_insights: str,
        risk_level: str,
        current_inventory: int,
        dynamic_rop: float,
        days_until_stockout: float,
        decision: str,
        urgency: str
    ) -> str:
        """
        Generate human-readable reasoning for the decision
        """

        reasoning_parts = []

        # Context
        reasoning_parts.append(f"SKU {sku_id} Analysis:")

        # Demand insights
        reasoning_parts.append(f"Demand: {demand_insights}")

        # Inventory status
        below_rop = current_inventory < dynamic_rop
        inventory_status = "BELOW" if below_rop else "ABOVE"
        reasoning_parts.append(
            f"Inventory: {current_inventory} units ({inventory_status} ROP of {dynamic_rop:.0f})"
        )

        # Risk assessment
        reasoning_parts.append(
            f"Risk: {risk_level.upper()} - Stockout in {days_until_stockout:.1f} days"
        )

        # Decision
        decision_explanations = {
            "IMMEDIATE_REORDER": "Decision: IMMEDIATE REORDER - Critical stockout risk detected",
            "ESCALATE_FOR_APPROVAL": "Decision: ESCALATE - High risk requires manager approval",
            "SCHEDULE_REORDER": "Decision: SCHEDULE REORDER - Inventory below threshold",
            "CONTINUE_MONITORING": "Decision: CONTINUE MONITORING - Inventory sufficient"
        }

        reasoning_parts.append(decision_explanations.get(decision, f"Decision: {decision}"))

        return " | ".join(reasoning_parts)


# Register agent
agent_registry.register(InventoryAgent)
