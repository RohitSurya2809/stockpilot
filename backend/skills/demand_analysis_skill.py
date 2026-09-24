"""
Demand Analysis Skill

Business capability for analyzing demand patterns and forecasting
"""

from typing import Type, Dict, Any
from pydantic import Field

from skills.base import Skill, SkillInput, SkillOutput, skill_registry
from tools.inventory_tools import GetSalesHistoryTool
from tools.analytics_tools import AnalyzePatternTool, ForecastDemandTool


# ========================================
# Input/Output Schemas
# ========================================

class DemandAnalysisInput(SkillInput):
    """Input for DemandAnalysisSkill"""
    sku_id: str = Field(description="SKU identifier")
    lookback_days: int = Field(default=30, description="Days of history to analyze")
    forecast_horizon: int = Field(default=30, description="Days to forecast ahead")


class DemandAnalysisOutput(SkillOutput):
    """Output for DemandAnalysisSkill"""
    sku_id: str
    pattern_analysis: Dict[str, Any]
    forecast: Dict[str, Any]
    insights: str


# ========================================
# Skill
# ========================================

class DemandAnalysisSkill(Skill):
    """
    Demand Analysis Skill

    Orchestrates:
    1. Get sales history
    2. Analyze patterns (trend, seasonality, volatility)
    3. Generate forecast
    4. Produce insights

    Use case: Understanding demand behavior
    """

    @property
    def input_schema(self) -> Type[SkillInput]:
        return DemandAnalysisInput

    @property
    def output_schema(self) -> Type[SkillOutput]:
        return DemandAnalysisOutput

    def _execute(self, input_data: DemandAnalysisInput) -> DemandAnalysisOutput:
        # Step 1: Get sales history
        sales_tool = GetSalesHistoryTool()
        sales_result = self.use_tool(
            sales_tool,
            sku_id=input_data.sku_id,
            days=input_data.lookback_days
        )

        if not sales_result.success:
            return DemandAnalysisOutput(
                success=False,
                error=sales_result.error,
                sku_id=input_data.sku_id,
                pattern_analysis={},
                forecast={},
                insights=""
            )

        daily_demand = sales_result.daily_demand

        # Step 2: Analyze patterns
        pattern_tool = AnalyzePatternTool()
        pattern_result = self.use_tool(
            pattern_tool,
            sales_data=daily_demand,
            window_days=min(len(daily_demand), 30)
        )

        if not pattern_result.success:
            return DemandAnalysisOutput(
                success=False,
                error=pattern_result.error,
                sku_id=input_data.sku_id,
                pattern_analysis={},
                forecast={},
                insights=""
            )

        # Step 3: Generate forecast
        forecast_tool = ForecastDemandTool()
        forecast_result = self.use_tool(
            forecast_tool,
            sales_data=daily_demand,
            forecast_horizon_days=input_data.forecast_horizon,
            moving_avg_window=min(14, len(daily_demand))
        )

        if not forecast_result.success:
            return DemandAnalysisOutput(
                success=False,
                error=forecast_result.error,
                sku_id=input_data.sku_id,
                pattern_analysis=pattern_result.data,
                forecast={},
                insights=""
            )

        # Step 4: Generate insights
        insights = self._generate_insights(
            pattern_result.data,
            forecast_result.data
        )

        return DemandAnalysisOutput(
            success=True,
            result={
                "pattern_analysis": pattern_result.data,
                "forecast": forecast_result.data,
                "insights": insights
            },
            sku_id=input_data.sku_id,
            pattern_analysis=pattern_result.data,
            forecast=forecast_result.data,
            insights=insights
        )

    def _generate_insights(
        self,
        pattern_analysis: Dict[str, Any],
        forecast: Dict[str, Any]
    ) -> str:
        """Generate human-readable insights"""
        insights = []

        # Trend insight
        trend = pattern_analysis['trend']
        if trend['trend'] == 'increasing':
            insights.append(f"Demand is trending UP ({trend['trend_percentage']:.1f}% over analysis window)")
        elif trend['trend'] == 'decreasing':
            insights.append(f"Demand is trending DOWN ({trend['trend_percentage']:.1f}% over analysis window)")
        else:
            insights.append("Demand is STABLE")

        # Seasonality insight
        seasonality = pattern_analysis['seasonality']
        if seasonality['has_seasonality']:
            insights.append(f"Weekly seasonal pattern detected (strength: {seasonality['autocorrelation']:.2f})")
        else:
            insights.append("No significant seasonality detected")

        # Volatility insight
        volatility = pattern_analysis['volatility']
        insights.append(f"Demand volatility: {volatility['volatility_level'].upper()} (CV: {volatility['coefficient_of_variation']:.1f}%)")

        # Forecast insight
        avg_forecast = sum(forecast['forecasts']) / len(forecast['forecasts'])
        insights.append(f"Forecasted average demand: {avg_forecast:.1f} units/day")
        insights.append(f"Forecast confidence: {forecast['confidence_level']:.0%}")

        return " | ".join(insights)


# Register skill
skill_registry.register(DemandAnalysisSkill)
