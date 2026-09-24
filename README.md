# STOCKPILOT
**Agentic Inventory & Procurement Automation**

> "Predict. Replenish. Automate."

---

## 🎯 Project Overview

StockPilot is an intelligent inventory and procurement automation platform built for Hack the Horizon 2.0 (Smart Automation track). It learns demand patterns, predicts stockout/overstock risks, dynamically calculates reorder points, and automatically prepares purchase orders for human approval.

**Problem Statement**: HTH-SA-03 - Usage-Pattern-Based Automated Inventory Restocking System

**Key Differentiator**: Unlike traditional fixed-threshold systems that react to stock levels, StockPilot predicts future inventory risk and proactively initiates procurement workflows.

---

## 📚 Documentation Structure

We've created comprehensive planning documents to guide the 24-hour development:

### 1. **PROJECT_SPEC.md**
Complete project specification including:
- Hackathon context and requirements
- Product vision and differentiation
- Core functionality details
- Demo scenario requirements
- Critical baseline comparison methodology
- Development philosophy

### 2. **IMPLEMENTATION_PLAN.md**
5-phase implementation strategy:
- **Phase 1** (Hours 0-4): Foundation & Infrastructure
- **Phase 2** (Hours 4-10): Core Analytics Engine
- **Phase 3** (Hours 10-16): Agentic Architecture
- **Phase 4** (Hours 16-21): Frontend Dashboard
- **Phase 5** (Hours 21-24): Integration, Testing & Demo

### 3. **TASK_PLAN.md**
Granular task breakdown with:
- Specific tasks for each phase
- Time estimates (realistic for 24-hour hackathon)
- Dependencies between tasks
- Priority levels (P0-P3)
- Critical path identification

### 4. **TECHNICAL_ARCHITECTURE.md**
Technical design decisions including:
- Complete architecture diagrams
- Database schema (9 tables)
- Core algorithms with Python pseudocode
- API endpoint definitions
- Agent/Skill/Tool architecture details
- MCP integration strategy
- Frontend component structure
- Risk mitigation strategies

---

## 🏗️ Architecture Overview

```
FRONTEND (React + TypeScript)
    ↓ REST API
INVENTORY AGENT (Reasoning & Orchestration)
    ↓ Skill Selection
SKILLS (Demand Analysis | Risk Assessment | Procurement)
    ↓ Tool Execution
TOOLS (Inventory | Forecast | Supplier | PO Generation)
    ↓ Analytics & Data
ANALYTICS ENGINE (Pattern Analysis | Forecasting | Risk Calculation)
    ↓ MCP Layer
COMPOSIO INTEGRATION (External System APIs)
    ↓
DATABASE (PostgreSQL)
```

**Key Architectural Concepts:**
- **Agents**: Decide what needs to be done (InventoryAgent)
- **Skills**: Orchestrate business capabilities (3 core skills)
- **Tools**: Perform deterministic operations (typed, testable)
- **MCP**: External system integration boundary (Composio)

---

## 🔧 Technology Stack

### Backend
- Python 3.10+ with FastAPI
- PostgreSQL (user: postgres, password: root)
- SQLAlchemy ORM
- Pandas, NumPy for data processing
- Scikit-learn (minimal usage)

### Frontend
- React 18 with TypeScript
- Vite build tool
- Material-UI for components
- Recharts for visualization
- Axios for API calls

### MCP Integration
- Composio Platform API
- API Key: `ak_Efmy6gQFVO6_gbiEnxAU`

---

## 🎯 Core Features

### 1. Pattern-Aware Demand Analysis
- Trend detection (increasing/decreasing/stable)
- Seasonality detection (weekly patterns)
- Volatility assessment

### 2. Intelligent Forecasting
- Moving average + trend adjustment
- Seasonality factors
- 30-day forecast horizon

### 3. Dynamic Reorder Points
**Formula**: `ROP = (Avg Demand × Lead Time) + Safety Stock`
- Adapts to demand changes
- Considers supplier lead time
- Calculates safety stock based on volatility

### 4. Predictive Risk Assessment
- Days until stockout calculation
- Stockout probability estimation
- Risk levels: Critical / High / Medium / Low

### 5. Automated Purchase Orders
- Draft PO generation with reasoning
- Human approval workflow
- Audit trail for all decisions

### 6. Baseline Comparison
**Critical for judging**: Quantified comparison against fixed-threshold strategy
- Side-by-side metrics
- Same scenarios, different strategies
- Charts showing improvement

---

## 📊 Demo Scenario

### The Demand Spike Story (2-3 minutes)

1. **Dashboard Overview**: Show 6 SKUs, most healthy
2. **Spike Introduction**: Focus on SKU-004 (Wireless Mouse)
   - Normal demand: 20 units/day
   - Demand increases: 22 → 24 → 27 → 31 → 35 → 38
3. **Pattern Detection**: StockPilot recognizes increasing trend (+27%)
4. **Risk Prediction**: "Stockout predicted in 4.2 days"
5. **Dynamic Response**: Reorder point adjusted from 100 → 184 units
6. **PO Generation**: Draft purchase order with full reasoning
7. **Human Approval**: Review and approve PO
8. **Baseline Comparison**: Show same scenario with fixed threshold
   - Fixed strategy: 3 stockouts
   - StockPilot: 0 stockouts

---

## 🚀 Quick Start (After Implementation)

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running
- Node.js 18+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python data/synthetic_generator.py  # Generate data
uvicorn api.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Database Setup
```bash
# Create database
psql -U postgres
CREATE DATABASE stockpilot;
\q

# Run migrations (after implementation)
python backend/models/database.py
```

---

## 📈 Success Criteria

### Must-Have (P0)
- ✅ Working end-to-end demo
- ✅ Dynamic reorder point calculation
- ✅ Fixed-threshold baseline comparison
- ✅ Quantified improvement metrics
- ✅ Purchase order generation
- ✅ Human approval workflow
- ✅ Explainable decisions
- ✅ Demand spike scenario working

### Should-Have (P1)
- ⭐ Agent/Skill/Tool architecture clearly demonstrated
- ⭐ Polished dashboard UI
- ⭐ Multiple demand patterns (6 SKUs)
- ⭐ Professional demo presentation

### Nice-to-Have (P3)
- 💎 Multi-supplier optimization
- 💎 Advanced ML forecasting
- 💎 Real-time updates via WebSocket

---

## 🎨 UI Design Philosophy

**NOT** a generic CRUD dashboard  
**IS** a modern enterprise operations console

### Key Screens
1. **Dashboard**: SKU overview with risk indicators
2. **SKU Detail**: Deep-dive analysis with charts and reasoning
3. **Comparison**: Adaptive vs Traditional side-by-side
4. **Procurement**: PO management and audit trail

### Design Elements
- Risk-based color coding (Red/Orange/Yellow/Green)
- Clear data visualization with Recharts
- Professional, clean layout with Material-UI
- Explainable AI - every decision has visible reasoning

---

## 🔒 Safety & Accountability

StockPilot is an **automation assistant**, not an autonomous system.

**What it does**:
- ✅ Analyze patterns
- ✅ Predict risks
- ✅ Recommend actions
- ✅ Generate PO drafts

**What it doesn't do**:
- ❌ Execute purchases without approval
- ❌ Override human decisions
- ❌ Hide reasoning

**All procurement actions require human approval.**

---

## 🎓 What Makes StockPilot Different

Traditional inventory systems: **React** to stock levels  
StockPilot: **Predicts** inventory risk and **proactively initiates** workflows

**Value Proposition**: PREDICTIVE + DECISION-AWARE + AUTOMATED + HUMAN-CONTROLLED

### Differentiation Factors
1. Pattern-aware demand analysis
2. Dynamic reorder points (not fixed)
3. Supplier lead-time awareness
4. Predictive stockout detection
5. Automated PO generation
6. Human approval gates
7. Quantified baseline comparison
8. Explainable decisions at every step

---

## 📋 Implementation Priority

### Critical Path (Must Complete)
1. Database + Synthetic Data (2h)
2. Analytics Algorithms (4h)
3. Simulation & Baseline (3h)
4. Agent/Skill/Tool Architecture (4h)
5. API Integration (1.5h)
6. Basic Frontend (4h)
7. Integration & Demo (2.5h)
8. Polish & Bug Fixes (2h)

**Total: ~23 hours** (1-hour buffer)

---

## 🧪 Testing Strategy

### Must Test
- All analytics algorithms produce sensible results
- Simulation shows StockPilot > Fixed threshold
- Agent orchestration works end-to-end
- PO approval workflow functions correctly
- Demo runs flawlessly 3 times in a row

### Critical Verifications
- Forecasts are realistic
- Risk calculations are correct
- Baseline comparison is fair (same data, different strategies)
- All agent decisions are logged with reasoning

---

## 🏆 Judging Criteria Alignment

### Pattern-Learning Quality ✓
- Trend detection with linear regression
- Seasonality detection with autocorrelation
- Volatility measurement with CV

### Quantified Improvement ✓
- Side-by-side simulation results
- Metrics: stockouts, service level, inventory levels
- Charts showing clear difference

### Realistic Lead-Time Handling ✓
- Supplier lead times in all calculations
- Dynamic reorder points consider delivery time
- Risk assessment based on lead-time urgency

### Bonus: Supplier Selection ⭐
- If time permits: multi-supplier optimization
- Cost vs. lead-time trade-offs
- Emergency supplier selection

---

## 📞 Next Steps

### Before Starting Implementation

1. **Review all documentation**:
   - PROJECT_SPEC.md
   - IMPLEMENTATION_PLAN.md
   - TASK_PLAN.md
   - TECHNICAL_ARCHITECTURE.md

2. **Confirm understanding**:
   - Architecture makes sense
   - Time estimates are realistic
   - Priorities are clear

3. **Set up environment**:
   - PostgreSQL running
   - Python environment ready
   - Node.js installed

4. **Start with Phase 1, Task P1.1.1**:
   - Initialize project structure
   - Follow task plan sequentially

### During Implementation

- **Preserve working demo** at all times
- **Test after each phase**
- **Adjust priorities** if time becomes tight
- **Focus on critical path** (P0 tasks)
- **Document as you build**

### Before Demo

- **Practice demo 3+ times**
- **Reset database and test reload**
- **Prepare presentation slides**
- **Verify all metrics are real** (not fabricated)

---

## 📊 Key Metrics for Demo

**Show these numbers** (from actual simulation):

| Metric | Fixed Threshold | StockPilot | Improvement |
|--------|----------------|------------|-------------|
| Stockouts | 3 | 0 | 100% |
| Service Level | 87% | 100% | +13% |
| Avg Inventory | 245 units | 198 units | -19% |
| Emergency Orders | 2 | 0 | 100% |

*(Example values - actual values will come from simulation)*

---

## 🎯 Vision Statement

**Traditional inventory systems wait for problems.**  
**StockPilot predicts and prevents them.**

By combining pattern recognition, predictive analytics, and intelligent automation with human oversight, StockPilot transforms reactive inventory management into proactive risk mitigation.

---

## 📝 License & Acknowledgments

Built for Hack the Horizon 2.0 - Smart Automation Track  
Problem Statement: HTH-SA-03

**Technologies**:
- FastAPI, React, PostgreSQL
- Material-UI, Recharts
- Composio Platform API

---

## 🔗 Quick Links

- [Full Project Specification](./PROJECT_SPEC.md)
- [Implementation Plan (5 Phases)](./IMPLEMENTATION_PLAN.md)
- [Detailed Task Breakdown](./TASK_PLAN.md)
- [Technical Architecture](./TECHNICAL_ARCHITECTURE.md)

---

**Ready to build?** Start with Phase 1, Task P1.1.1 in TASK_PLAN.md

**Questions?** Review the technical architecture for implementation details.

**Behind schedule?** Check the "Risk Mitigation & Simplification Options" section in TECHNICAL_ARCHITECTURE.md

---

*Last Updated: 2026-09-24*
