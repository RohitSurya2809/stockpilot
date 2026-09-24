# 🚀 STOCKPILOT
**Agentic Inventory & Procurement Automation**

> "Predict. Replenish. Automate."

[![Hack the Horizon 2.0](https://img.shields.io/badge/Hackathon-Hack%20the%20Horizon%202.0-blue)](https://hackathon.link)
[![Track](https://img.shields.io/badge/Track-Smart%20Automation-green)](https://track.link)
[![Problem](https://img.shields.io/badge/Problem-HTH--SA--03-orange)](https://problem.link)

---

## 📋 Problem Statement

**HTH-SA-03: Usage-Pattern-Based Automated Inventory Restocking System**

Traditional fixed reorder-point thresholds cause stockouts during demand spikes and overstock during slow periods because they ignore actual usage patterns.

---

## 💡 Our Solution

**StockPilot** is an intelligent inventory and procurement automation platform that:

✅ **Learns demand patterns** (trend, seasonality, volatility)  
✅ **Predicts future stockout risk** before it happens  
✅ **Dynamically calculates reorder points** based on demand and supplier lead time  
✅ **Automatically prepares purchase orders** with explainable reasoning  
✅ **Orchestrates approval workflows** via n8n automation  
✅ **Proves improvement** against fixed-threshold baseline  

### The Key Difference

| Traditional Systems | StockPilot |
|-------------------|-----------|
| **React** to stock levels | **Predict** inventory risk |
| Fixed thresholds | Dynamic reorder points |
| No demand intelligence | Pattern-aware analysis |
| Manual procurement | Automated workflow |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (React + TypeScript)               │
│          Dashboard │ Analysis │ Comparison               │
└──────────────────────────┬──────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────┐
│           STOCKPILOT BACKEND (Python + FastAPI)          │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │         INVENTORY AGENT                          │   │
│  │         (Decides WHAT should happen)             │   │
│  └─────┬──────────────────────────────────┬────────┘   │
│        │                                   │             │
│   ┌────▼─────┐  ┌────────┐  ┌───────────▼────┐        │
│   │ Demand   │  │  Risk  │  │  Procurement   │        │
│   │  Skill   │  │ Skill  │  │     Skill      │        │
│   └────┬─────┘  └───┬────┘  └────────┬───────┘        │
│        │            │                 │                 │
│   ┌────▼────────────▼─────────────────▼─────────┐     │
│   │              TOOL LAYER                      │     │
│   │  Inventory │ Forecast │ Supplier │ PO Gen   │     │
│   └────┬──────────┬─────────────────┬───────────┘     │
│        │          │                 │                  │
│   ┌────▼──────────▼─────────────────▼──────────┐      │
│   │        ANALYTICS ENGINE                     │      │
│   │  Pattern │ Forecast │ Dynamic ROP │ Risk   │      │
│   └────┬─────────────────────────────────────┬─┘      │
│        │                                     │         │
│   ┌────▼─────────────────────────────────────▼───┐    │
│   │           MCP INTEGRATION LAYER              │    │
│   └────┬─────────────────────────────────────────┘    │
│        │                                               │
└────────┼───────────────────────────────────────────────┘
         │
    ┌────▼────┐
    │   n8n   │
    │ (Executes HOW it happens)
    │ Workflow │ Notify │ Approve │ Log
    └─────────┘
         │
    ┌────▼────┐
    │PostgreSQL│
    └─────────┘
```

### Key Architectural Concepts

**Agent/Skill/Tool Paradigm:**
- **Agents**: Decide what needs to be done (InventoryAgent)
- **Skills**: Orchestrate business capabilities (3 core skills)
- **Tools**: Perform deterministic operations (typed, testable)
- **MCP**: External system integration boundary

**Intelligence vs Execution:**
- **StockPilot Backend**: Makes intelligent decisions (WHAT)
- **n8n Workflows**: Executes business processes (HOW)
- **Clear Separation**: AI doesn't handle email/notifications directly

---

## 🎯 Core Features

### 1. Pattern-Aware Demand Analysis
- **Trend Detection**: Linear regression identifies increasing/decreasing/stable demand
- **Seasonality Detection**: Autocorrelation-based weekly pattern recognition
- **Volatility Assessment**: Coefficient of variation measurement

### 2. Intelligent Forecasting
- **Method**: Moving average + trend adjustment + seasonality factors
- **Horizon**: 30-day forecast
- **Explainable**: Every forecast backed by mathematical reasoning

### 3. Dynamic Reorder Points
```
ROP = (Average Demand × Lead Time) + Safety Stock

Safety Stock = Z-score(0.95) × σ_demand × √(lead_time)
```
- Adapts to demand changes automatically
- Considers supplier lead time
- Service level: 95%

### 4. Predictive Risk Assessment
- Days until stockout calculation
- Stockout probability estimation
- Risk levels: Critical / High / Medium / Low
- Triggers proactive procurement

### 5. Automated Procurement Workflow
```
Agent Decision → PO Draft → n8n Workflow → Notification → Approval → Execution
```
- Draft PO generation with reasoning
- Human approval gate
- Full audit trail

### 6. Baseline Comparison (Critical for Evaluation)
**Quantified improvement against fixed-threshold strategy**

| Metric | Fixed Threshold | StockPilot | Improvement |
|--------|----------------|------------|-------------|
| Stockouts | 3 | 0 | **100%** ✅ |
| Service Level | 87% | 100% | **+13%** ✅ |
| Avg Inventory | 245 units | 198 units | **-19%** ✅ |
| Emergency Orders | 2 | 0 | **100%** ✅ |

*(Values from simulation - see demo)*

---

## 🛠️ Technology Stack

### Backend
- **Python 3.10+** with FastAPI
- **PostgreSQL** for data persistence
- **Pandas + NumPy** for analytics
- **Scikit-learn** for pattern detection
- **SQLAlchemy** ORM

### Frontend
- **React 18** with TypeScript
- **Vite** build tool
- **Material-UI** component library
- **Recharts** for visualization

### Automation & Integration
- **n8n** for workflow automation
- **MCP** integration layer
- **Composio** platform for external capabilities

---

## 📊 Synthetic Dataset

We've generated 90 days of realistic inventory data with 6 distinct demand patterns:

1. **SKU-001 (Stable)**: 50 ±3 units/day
2. **SKU-002 (Increasing)**: 20/day with +2% daily growth
3. **SKU-003 (Seasonal)**: 40/day baseline, +50% every 7 days
4. **SKU-004 (Spike)**: 30/day, then sudden 3x spike ⚠️
5. **SKU-005 (Decreasing)**: 60/day with -1.5% daily decline
6. **SKU-006 (Volatile)**: 40/day with ±15 random variance

**SKU-004 (Spike)** is our primary demo scenario.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (running on localhost)
- Node.js 18+
- n8n (optional for workflow demo)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with database credentials

# Initialize database
python models/database.py

# Generate synthetic data
python data/synthetic_generator.py

# Start server
uvicorn api.main:app --reload
```

Backend runs on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on `http://localhost:5173`

### 3. n8n Setup (Optional)

```bash
# Install n8n
npm install -g n8n

# Start n8n
n8n start

# Import workflow
# - Open http://localhost:5678
# - Import workflows/stockpilot_procurement.json
# - Configure webhook URL in backend .env
```

---

## 🎬 Demo Flow (2-3 minutes)

### Act 1: The Problem (30 sec)
> "Traditional inventory systems react to fixed thresholds. Watch what happens during a demand spike..."

**Show**: Dashboard with 6 SKUs, highlight SKU-004 (Wireless Mouse)

### Act 2: Pattern Detection (45 sec)
**Click**: SKU-004 detail page

**Show**:
- Demand trend chart: 20 → 22 → 24 → 27 → 31 → 35 → 38
- StockPilot detects: "27% demand increase"
- Forecast: Continued growth
- Risk assessment: "Stockout predicted in 4.2 days"
- Dynamic reorder point: 184 units (vs. fixed threshold: 100)

### Act 3: Intelligent Action (30 sec)
**Click**: [GENERATE PO]

**Show** PO Draft:
```
Purchase Order #PO-1042
Product: Wireless Mouse
Quantity: 350 units
Cost: ₹35,000
Supplier: ABC Supplies (7-day lead time)

Reasoning:
"SKU-004 has experienced a 27% increase in recent demand. 
Supplier lead time is 7 days. Current inventory (184 units) 
is projected to fall below safety stock in 4.2 days. 
Replenishment order recommended."

Generated by: InventoryAgent
```

**Click**: [APPROVE]

**Show**: n8n workflow executes (open n8n tab)
- Notification sent
- Approval logged
- PO status updated

### Act 4: The Proof (30 sec)
**Navigate**: Baseline Comparison page

**Show**: Same scenario under both strategies

| Metric | Fixed | StockPilot |
|--------|-------|-----------|
| Stockouts | 3 | 0 |
| Service Level | 87% | 100% |

**Explain**: "By learning demand patterns and predicting risk, StockPilot prevents stockouts while optimizing inventory levels."

### Act 5: Architecture (30 sec)
**Show**: Agent logs and architecture diagram

**Explain**: "StockPilot uses an Agent/Skill/Tool architecture where the AI decides WHAT should happen, and n8n executes HOW it happens across systems."

---

## 📈 Evaluation Criteria Alignment

### ✅ Pattern-Learning Quality
- **Trend Detection**: Linear regression with R² scoring
- **Seasonality Detection**: Autocorrelation-based (period=7)
- **Volatility**: Coefficient of variation

### ✅ Quantified Improvement
- **Direct Comparison**: Same data, both strategies
- **Simulation-Based**: 30-day scenarios for all 6 SKUs
- **Metrics**: Stockouts, service level, inventory levels, emergency orders

### ✅ Realistic Lead-Time Handling
- **Supplier Lead Times**: 3-14 days range
- **Forecast Horizon**: Covers lead time + buffer
- **Dynamic ROP**: `Expected demand during lead time + Safety stock`
- **Risk Assessment**: "Days until stockout" vs. lead time

### 🌟 Bonus: Supplier Selection
- Multi-supplier database
- Cost vs. lead-time trade-offs
- Primary supplier logic implemented
- Extensible for optimization algorithms

---

## 🔒 Safety & Accountability

**StockPilot is an automation assistant, not an autonomous system.**

### What it does:
✅ Analyze patterns  
✅ Predict risks  
✅ Recommend actions  
✅ Generate PO drafts  

### What it doesn't do:
❌ Execute purchases without approval  
❌ Override human decisions  
❌ Hide reasoning  

**All procurement actions require human approval.**

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# End-to-end test
python scripts/test_complete_flow.py
```

---

## 📚 Documentation

- **API Documentation**: `/docs` (FastAPI auto-generated)
- **Architecture Guide**: `ARCHITECTURE.md`
- **Algorithm Details**: `docs/algorithms.md`
- **n8n Workflows**: `workflows/README.md`

---

## 🤝 Team

- **Backend & AI**: [Team Member]
- **Frontend**: [Team Member]
- **Analytics**: [Team Member]
- **Integration**: [Team Member]

---

## 🏆 Hackathon Details

**Event**: Hack the Horizon 2.0  
**Track**: Smart Automation  
**Problem**: HTH-SA-03  
**Timeline**: 24 hours  
**Tech Stack**: Python, FastAPI, React, PostgreSQL, n8n  

---

## 📜 License

MIT License - Built for Hack the Horizon 2.0

---

## 🙏 Acknowledgments

- **FastAPI** for excellent Python web framework
- **Material-UI** for React components
- **Recharts** for data visualization
- **n8n** for workflow automation
- **Composio** for MCP integration

---

## 📧 Contact

For questions or feedback: [contact@example.com]

---

**Built with ❤️ for Hack the Horizon 2.0**
