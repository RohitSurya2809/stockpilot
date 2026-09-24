// TypeScript types for StockPilot

export interface SKU {
  sku_id: string;
  product_name: string;
  category: string;
  current_stock: number;
  safety_stock: number;
  reorder_point: number;
  recent_daily_demand: number;
  demand_trend: string | null;
  risk_level: string | null;
  days_until_stockout: number | null;
  supplier_name: string;
  supplier_lead_time: number;
}

export interface AnalysisResult {
  sku_id: string;
  needs_reorder: boolean;
  reasoning: string;
  pattern_analysis: {
    trend: TrendAnalysis;
    seasonality: SeasonalityAnalysis;
    volatility: VolatilityAnalysis;
  };
  forecast: ForecastResult;
  reorder_point: ReorderPointResult;
  risk_assessment: RiskAssessment;
  recommended_order: RecommendedOrder | null;
}

export interface TrendAnalysis {
  trend: 'increasing' | 'decreasing' | 'stable';
  trend_percentage: number;
  trend_strength: number;
}

export interface SeasonalityAnalysis {
  has_seasonality: boolean;
  period: number;
  autocorrelation: number;
}

export interface VolatilityAnalysis {
  coefficient_of_variation: number;
  volatility_level: 'low' | 'medium' | 'high';
  mean_demand: number;
  std_deviation: number;
}

export interface ForecastResult {
  forecasts: number[];
  method: string;
  confidence_level: number;
  source?: string;
  ml_available?: boolean;
  ml_metrics?: {
    model_name: string;
    val_mae: number;
    val_rmse: number;
    train_size: number;
    val_size: number;
  };
}

export interface ReorderPointResult {
  dynamic_reorder_point: number;
  expected_demand_during_lead_time: number;
  safety_stock: number;
  avg_daily_demand: number;
}

export interface RiskAssessment {
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  days_until_stockout: number;
  stockout_probability: number;
  recommended_action: string;
}

export interface RecommendedOrder {
  supplier_id: number;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  lead_time_days: number;
}

export interface SimulationResult {
  sku_id: string;
  simulation_days: number;
  fixed_threshold: StrategyResult;
  adaptive: StrategyResult;
  improvement: ImprovementMetrics;
}

export interface StrategyResult {
  stockouts: number;
  service_level: number;
  average_inventory: number;
  orders_placed: number;
}

export interface ImprovementMetrics {
  stockout_reduction: number;
  service_level_improvement: number;
}

export interface AgentDecision {
  agent_id: string;
  decision_type: string;
  reasoning: string;
  timestamp: string;
}
