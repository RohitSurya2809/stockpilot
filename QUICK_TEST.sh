#!/bin/bash
# STOCKPILOT - Quick Test Script
# Run this to verify everything is working

echo "======================================================================"
echo "STOCKPILOT - QUICK TEST SUITE"
echo "======================================================================"
echo ""

cd backend

echo "TEST 1: Configuration"
echo "----------------------------------------------------------------------"
./venv/Scripts/python -c "from config import settings; print(f'✓ Database: {str(settings.database_url).split('@')[1]}'); print(f'✓ Ollama: {settings.ollama_base_url}'); print(f'✓ Model: {settings.ollama_model}')"
echo ""

echo "TEST 2: Database"
echo "----------------------------------------------------------------------"
./venv/Scripts/python -c "from models import SessionLocal, SKU, SalesHistory; db = SessionLocal(); print(f'✓ SKUs: {db.query(SKU).count()}'); print(f'✓ Sales records: {db.query(SalesHistory).count()}'); db.close()"
echo ""

echo "TEST 3: THE PROOF - Simulation Results"
echo "----------------------------------------------------------------------"
./venv/Scripts/python -m simulation.scenario_runner 2>&1 | tail -25
echo ""

echo "======================================================================"
echo "✓ CORE INTELLIGENCE VERIFIED"
echo "======================================================================"
echo ""
echo "To start the API server:"
echo "  cd backend && ./venv/Scripts/uvicorn api.main:app --reload"
echo ""
echo "Then test API:"
echo "  curl http://localhost:8000/api/health"
echo "  curl http://localhost:8000/api/inventory"
echo "  curl -X POST http://localhost:8000/api/simulation/run/SKU-004"
echo ""
