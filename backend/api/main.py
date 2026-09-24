"""
StockPilot FastAPI Application

Main application entry point for the StockPilot backend API.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from config import settings
from models import get_db, test_connection
from api.routes import inventory, analysis, simulation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StockPilot API",
    description="Agentic Inventory & Procurement Automation API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("="*70)
    logger.info("STOCKPILOT API STARTING")
    logger.info("="*70)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"LLM Provider: {settings.llm_provider}")

    # Test database connection
    if test_connection():
        logger.info("[OK] Database connection established")
    else:
        logger.error("[ERROR] Database connection failed!")

    logger.info("="*70)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("StockPilot API shutting down...")


# Health Check Endpoint
@app.get("/api/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Returns system status and database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "StockPilot API",
        "version": "1.0.0",
        "environment": settings.environment,
        "database": db_status,
        "llm_provider": settings.llm_provider
    }


# Root Endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "StockPilot API",
        "version": "1.0.0",
        "tagline": "Predict. Replenish. Automate.",
        "documentation": "/api/docs",
        "health_check": "/api/health"
    }


# Include routers
app.include_router(inventory.router, prefix="/api", tags=["Inventory"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])
# Procurement router will be added in Phase 3:
# from api.routes import procurement
# app.include_router(procurement.router, prefix="/api", tags=["Procurement"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
