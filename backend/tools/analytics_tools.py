"""
Analytics Tools

Concrete tools for analytics operations (wrapping analytics modules)
"""

from typing import Optional, Type, List, Dict, Any
from pydantic import Field

from tools.base import Tool, ToolInput, ToolOutput, tool_registry
from analytics.demand_pattern_analyzer import analyze_trend, detect_seasonality, calculate_volatility
from analytics.hybrid_forecaster import hybrid_forecast_demand
from analytics.reorder_calculator import calculate_dynamic_reorder_point
from analytics.risk_engine import assess_stockout_risk


# ========================================
# Input/Output Schemas
# ========================================

class AnalyzePatternInput(ToolInput):
    """Input for AnalyzePatternTool"""
    sales_data: List[float] = Field(description="Historical daily demand values")
    window_days: int = Field(default=30, description="Analysis window in days")


class AnalyzePatternOutput(ToolOutput):
    """Output for AnalyzePatternTool"""
    trend: Optional[Dict[str, Any]] = None
    seasonality: Optional[Dict[str, Any]] = None
    volatility: Optional[Dict[str, Any]] = None


class ForecastDemandInput(ToolInput):
    """Input for ForecastDemandTool"""
    sales_data: List[float] = Field(description="Historical daily demand values")
    forecast_horizon_days: int = Field(default=30, description="Forecast horizon")
    moving_avg_window: int = Field(default=14, description="Moving average window")


class ForecastDemandOutput(ToolOutput):
    """Output for ForecastDemandTool"""
    forecasts: Optional[List[float]] = None
    method: Optional[str] = None
    confidence_level: Optional[float] = None
    ml_available: Optional[bool] = None
    ml_model_name: Optional[str] = None
    ml_val_mae: Optional[float] = None
    ml_val_rmse: Optional[float] = None
    forecast_source: Optional[str] = None  # 'ml' or 'statistical'


class CalculateROPInput(ToolInput):
    """Input for CalculateROPTool"""
    sales_data: List[float] = Field(description="Historical daily demand values")
    supplier_lead_time_days: int = Field(description="Supplier lead time in days")
    service_level: float = Field(default=0.95, description="Target service level")


class CalculateROPOutput(ToolOutput):
    """Output for CalculateROPTool"""
    dynamic_reorder_point: Optional[float] = None
    expected_demand_during_lead_time: Optional[float] = None
    safety_stock: Optional[float] = None
    avg_daily_demand: Optional[float] = None


class AssessRiskInput(ToolInput):
    """Input for AssessRiskTool"""
    current_inventory: int = Field(description="Current stock level")
    sales_data: List[float] = Field(description="Historical daily demand values")
    supplier_lead_time_days: int = Field(description="Supplier lead time in days")
    dynamic_reorder_point: Optional[float] = Field(default=None, description="Dynamic ROP (optional)")


class AssessRiskOutput(ToolOutput):
    """Output for AssessRiskTool"""
    risk_level: Optional[str] = None
    days_until_stockout: Optional[float] = None
    stockout_probability: Optional[float] = None
    recommended_action: Optional[str] = None


# ========================================
# Tools
# ========================================

class AnalyzePatternTool(Tool):
    """
    Analyzes demand patterns (trend, seasonality, volatility)

    Uses statistical methods:
    - Linear regression for trend
    - Autocorrelation for seasonality
    - Coefficient of variation for volatility
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return AnalyzePatternInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return AnalyzePatternOutput

    def _execute(self, input_data: AnalyzePatternInput) -> AnalyzePatternOutput:
        try:
            trend = analyze_trend(
                input_data.sales_data,
                window_days=input_data.window_days
            )

            seasonality = detect_seasonality(input_data.sales_data)

            volatility = calculate_volatility(input_data.sales_data)

            return AnalyzePatternOutput(
                success=True,
                data={
                    "trend": trend,
                    "seasonality": seasonality,
                    "volatility": volatility
                },
                trend=trend,
                seasonality=seasonality,
                volatility=volatility
            )

        except Exception as e:
            return AnalyzePatternOutput(
                success=False,
                error=str(e)
            )


class ForecastDemandTool(Tool):
    """
    Forecasts future demand using hybrid ML + statistical methods

    Methods:
    - ML: RandomForestRegressor (when >= 30 days data available)
    - Statistical: Moving average + trend adjustment + seasonality (fallback)

    Returns validation metrics (MAE, RMSE) when ML is used
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return ForecastDemandInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return ForecastDemandOutput

    def _execute(self, input_data: ForecastDemandInput) -> ForecastDemandOutput:
        try:
            # Use hybrid forecaster (statistical + ML)
            hybrid_result = hybrid_forecast_demand(
                sales_data=input_data.sales_data,
                forecast_horizon_days=input_data.forecast_horizon_days,
                moving_avg_window=input_data.moving_avg_window,
                use_ml=True
            )

            # Extract selected forecast (ML or statistical fallback)
            selected = hybrid_result['selected_forecast']

            # Extract ML metrics if available
            ml_forecast = hybrid_result.get('ml_forecast', {})
            ml_available = ml_forecast.get('available', False)

            return ForecastDemandOutput(
                success=True,
                data=hybrid_result,
                forecasts=selected['forecasts'],
                method=selected['method'],
                confidence_level=selected['confidence_level'],
                ml_available=ml_available,
                ml_model_name=ml_forecast.get('model_name') if ml_available else None,
                ml_val_mae=ml_forecast.get('val_mae') if ml_available else None,
                ml_val_rmse=ml_forecast.get('val_rmse') if ml_available else None,
                forecast_source=selected['source']
            )

        except Exception as e:
            return ForecastDemandOutput(
                success=False,
                error=str(e)
            )


class CalculateROPTool(Tool):
    """
    Calculates dynamic reorder point

    Formula: ROP = (Avg Demand × Lead Time) + Safety Stock
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return CalculateROPInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return CalculateROPOutput

    def _execute(self, input_data: CalculateROPInput) -> CalculateROPOutput:
        try:
            rop_result = calculate_dynamic_reorder_point(
                sales_data=input_data.sales_data,
                supplier_lead_time_days=input_data.supplier_lead_time_days,
                service_level=input_data.service_level
            )

            return CalculateROPOutput(
                success=True,
                data=rop_result,
                dynamic_reorder_point=rop_result['dynamic_reorder_point'],
                expected_demand_during_lead_time=rop_result['expected_demand_during_lead_time'],
                safety_stock=rop_result['safety_stock'],
                avg_daily_demand=rop_result['avg_daily_demand']
            )

        except Exception as e:
            return CalculateROPOutput(
                success=False,
                error=str(e)
            )


class AssessRiskTool(Tool):
    """
    Assesses stockout risk

    Analyzes:
    - Days until stockout
    - Risk level (critical/high/medium/low)
    - Stockout probability
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return AssessRiskInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return AssessRiskOutput

    def _execute(self, input_data: AssessRiskInput) -> AssessRiskOutput:
        try:
            risk_result = assess_stockout_risk(
                current_inventory=input_data.current_inventory,
                sales_data=input_data.sales_data,
                supplier_lead_time_days=input_data.supplier_lead_time_days,
                dynamic_reorder_point=input_data.dynamic_reorder_point
            )

            return AssessRiskOutput(
                success=True,
                data=risk_result,
                risk_level=risk_result['risk_level'],
                days_until_stockout=risk_result['days_until_stockout'],
                stockout_probability=risk_result['stockout_probability'],
                recommended_action=risk_result['recommended_action']
            )

        except Exception as e:
            return AssessRiskOutput(
                success=False,
                error=str(e)
            )


# Register tools
tool_registry.register(AnalyzePatternTool)
tool_registry.register(ForecastDemandTool)
tool_registry.register(CalculateROPTool)
tool_registry.register(AssessRiskTool)
