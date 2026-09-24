"""
Analysis API Routes

Endpoints for demand analysis, forecasting, and risk assessment.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta

from models import get_db, SKU, Inventory, SalesHistory, SKUSupplier, Supplier
from analytics.demand_pattern_analyzer import analyze_demand_pattern, generate_pattern_summary
from analytics.forecaster import forecast_demand, generate_forecast_summary
from analytics.reorder_calculator import calculate_dynamic_reorder_point, generate_reorder_explanation
from analytics.risk_engine import comprehensive_risk_assessment, generate_risk_summary
from api.utils import convert_numpy_types

router = APIRouter()


@router.post("/analysis/{sku_id}/pattern")
async def analyze_sku_pattern(
    sku_id: str,
    days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Analyze demand pattern for a SKU.

    Returns trend, seasonality, and volatility analysis.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for SKU {sku_id} (need at least 7 days)"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # Analyze pattern
    analysis = analyze_demand_pattern(sales_data)

    if 'error' in analysis:
        raise HTTPException(status_code=400, detail=analysis['error'])

    # Generate summary
    summary = generate_pattern_summary(analysis)

    return {
        'sku_id': sku_id,
        'analysis': analysis,
        'summary': summary,
        'data_points': len(sales_data)
    }


@router.post("/analysis/{sku_id}/forecast")
async def forecast_sku_demand(
    sku_id: str,
    horizon_days: int = 30,
    historical_days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Generate demand forecast for a SKU.

    Returns daily forecasted demand for specified horizon.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=historical_days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for SKU {sku_id}"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # Generate forecast
    forecast_result = forecast_demand(
        sales_data=sales_data,
        forecast_horizon_days=horizon_days,
        moving_avg_window=14,
        include_trend=True,
        include_seasonality=True
    )

    if 'error' in forecast_result:
        raise HTTPException(status_code=400, detail=forecast_result['error'])

    # Generate summary
    summary = generate_forecast_summary(forecast_result)

    return {
        'sku_id': sku_id,
        'forecast': forecast_result,
        'summary': summary
    }


@router.post("/analysis/{sku_id}/reorder-point")
async def calculate_sku_reorder_point(
    sku_id: str,
    service_level: float = 0.95,
    historical_days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Calculate dynamic reorder point for a SKU.

    Returns dynamic ROP based on demand patterns and supplier lead time.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get supplier info
    sku_supplier = db.query(SKUSupplier, Supplier).join(
        Supplier, SKUSupplier.supplier_id == Supplier.id
    ).filter(
        SKUSupplier.sku_id == sku_id,
        SKUSupplier.is_primary == True
    ).first()

    if not sku_supplier:
        raise HTTPException(
            status_code=404,
            detail=f"No primary supplier found for SKU {sku_id}"
        )

    supplier_lead_time = sku_supplier[1].lead_time_days

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=historical_days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for SKU {sku_id}"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # Calculate dynamic ROP
    rop_calc = calculate_dynamic_reorder_point(
        sales_data=sales_data,
        supplier_lead_time_days=supplier_lead_time,
        service_level=service_level
    )

    if 'error' in rop_calc:
        raise HTTPException(status_code=400, detail=rop_calc['error'])

    # Generate explanation
    explanation = generate_reorder_explanation(rop_calc)

    return {
        'sku_id': sku_id,
        'reorder_point_calculation': rop_calc,
        'explanation': explanation,
        'supplier': sku_supplier[1].name,
        'supplier_lead_time': supplier_lead_time
    }


@router.post("/analysis/{sku_id}/risk")
async def assess_sku_risk(
    sku_id: str,
    service_level: float = 0.95,
    historical_days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Assess stockout/overstock risk for a SKU.

    Returns comprehensive risk assessment with recommendations.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get current inventory
    inventory = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if not inventory:
        raise HTTPException(
            status_code=404,
            detail=f"No inventory record for SKU {sku_id}"
        )

    # Get supplier info
    sku_supplier = db.query(SKUSupplier, Supplier).join(
        Supplier, SKUSupplier.supplier_id == Supplier.id
    ).filter(
        SKUSupplier.sku_id == sku_id,
        SKUSupplier.is_primary == True
    ).first()

    if not sku_supplier:
        raise HTTPException(
            status_code=404,
            detail=f"No primary supplier found for SKU {sku_id}"
        )

    supplier_lead_time = sku_supplier[1].lead_time_days

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=historical_days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for SKU {sku_id}"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # Comprehensive risk assessment
    risk_assessment = comprehensive_risk_assessment(
        sku_id=sku_id,
        current_inventory=inventory.current_stock,
        sales_data=sales_data,
        supplier_lead_time_days=supplier_lead_time,
        service_level=service_level
    )

    if 'error' in risk_assessment:
        raise HTTPException(status_code=400, detail=risk_assessment['error'])

    # Generate summary
    summary = generate_risk_summary(risk_assessment)

    return {
        'sku_id': sku_id,
        'risk_assessment': risk_assessment,
        'summary': summary,
        'supplier': sku_supplier[1].name
    }


@router.post("/analysis/{sku_id}/complete")
async def complete_sku_analysis(
    sku_id: str,
    service_level: float = 0.95,
    forecast_horizon: int = 30,
    historical_days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Run complete analysis for a SKU.

    Combines pattern analysis, forecasting, ROP calculation, and risk assessment.
    This is the main analysis endpoint for the dashboard.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get current inventory
    inventory = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if not inventory:
        raise HTTPException(
            status_code=404,
            detail=f"No inventory record for SKU {sku_id}"
        )

    # Get supplier info
    sku_supplier = db.query(SKUSupplier, Supplier).join(
        Supplier, SKUSupplier.supplier_id == Supplier.id
    ).filter(
        SKUSupplier.sku_id == sku_id,
        SKUSupplier.is_primary == True
    ).first()

    if not sku_supplier:
        raise HTTPException(
            status_code=404,
            detail=f"No primary supplier found for SKU {sku_id}"
        )

    supplier = sku_supplier[1]

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=historical_days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 7:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for SKU {sku_id} (need at least 7 days)"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # 1. Pattern analysis
    pattern_analysis = analyze_demand_pattern(sales_data)
    pattern_summary = generate_pattern_summary(pattern_analysis)

    # 2. Forecast
    forecast_result = forecast_demand(
        sales_data=sales_data,
        forecast_horizon_days=forecast_horizon,
        include_trend=True,
        include_seasonality=True
    )
    forecast_summary = generate_forecast_summary(forecast_result)

    # 3. Dynamic ROP
    rop_calc = calculate_dynamic_reorder_point(
        sales_data=sales_data,
        supplier_lead_time_days=supplier.lead_time_days,
        service_level=service_level
    )
    rop_explanation = generate_reorder_explanation(rop_calc)

    # 4. Risk assessment
    risk_assessment = comprehensive_risk_assessment(
        sku_id=sku_id,
        current_inventory=inventory.current_stock,
        sales_data=sales_data,
        supplier_lead_time_days=supplier.lead_time_days,
        service_level=service_level
    )
    risk_summary = generate_risk_summary(risk_assessment)

    result = {
        'sku_id': sku_id,
        'product_name': sku.name,
        'current_inventory': inventory.current_stock,
        'supplier': {
            'name': supplier.name,
            'lead_time_days': supplier.lead_time_days
        },
        'pattern_analysis': {
            'data': pattern_analysis,
            'summary': pattern_summary
        },
        'forecast': {
            'data': forecast_result,
            'summary': forecast_summary
        },
        'dynamic_reorder_point': {
            'data': rop_calc,
            'explanation': rop_explanation
        },
        'risk_assessment': {
            'data': risk_assessment,
            'summary': risk_summary
        }
    }

    return convert_numpy_types(result)
