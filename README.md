# 🚀 STOCKPILOT
**Agentic Inventory & Procurement Automation**

> *"Predict. Replenish. Automate."*

**Hack the Horizon 2.0** | Smart Automation Track | Problem Statement HTH-SA-03

---

## 💡 The Problem

Traditional inventory systems use **fixed reorder-point thresholds** that ignore actual demand behavior:
- ❌ **Stockouts during demand spikes** → Lost sales
- ❌ **Overstock during slow periods** → Capital tied up
- ❌ **Manual procurement workflows** → Delays and errors
- ❌ **No adaptability** → Cannot respond to changing patterns

**Real-world impact:** 30% of retail stockouts are preventable, and overstocking ties up 20-30% of working capital.

---

## ✨ Our Solution

**StockPilot** doesn't wait for inventory to hit a fixed threshold. Instead, it:

✅ **Learns demand patterns** (trend, seasonality, volatility)  
✅ **Predicts future stockout risk** before it happens  
✅ **Dynamically calculates reorder points** based on real-time demand  
✅ **Automates procurement workflows** with human approval gates  
✅ **Proves quantified improvement** vs traditional systems

### Key Differentiator
> Traditional systems **react** to stock levels.  
> StockPilot **predicts** inventory risk and **proactively** initiates procurement.

---

## 🏗️ Architecture

StockPilot uses an **Agent/Skill/Tool/MCP architecture** for maintainable automation:

```
┌─────────────────────────────────────────────┐
│       STOCKPILOT BACKEND (Python)            │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │      INVENTORY AGENT               │    │
│  │   (Decides WHAT to do)             │    │
│  └─────────────┬──────────────────────┘    │
│                │                             │
│         ┌──────┴──────┐                     │
│         ▼              ▼                     │
│    SKILLS          TOOLS                     │
│  (Business)    (Operations)                 │
│         │              │                     │
│         └──────┬───────┘                     │
│                ▼                             │
│      ANALYTICS ENGINE                        │
│   Pattern | Forecast | Risk                 │
│                │                             │
│                ▼                             │
│           MCP LAYER                          │
│      (External Systems)                      │
│                │                             │
│                ▼                             │
│          n8n WORKFLOWS                       │
│      (Executes HOW)                          │
└─────────────────────────────────────────────┘
```

**Intelligence Layer:** Python analytics (deterministic, explainable)  
**Decision Layer:** Agent orchestrates Skills → Tools  
**Automation Layer:** n8n workflows + human approval gates

---

## 📊 Core Intelligence

### 1. Pattern-Aware Demand Analysis
- **Trend Detection:** Linear regression identifies increasing/decreasing/stable demand
- **Seasonality Detection:** Autocorrelation-based pattern recognition
- **Volatility Assessment:** Coefficient of variation measurement

### 2. Intelligent Forecasting
- Moving average + trend adjustment + seasonality
- 30-day forecast horizon
- Confidence scoring

### 3. Dynamic Reorder Points
```
ROP = (Average Demand × Lead Time) + Safety Stock
Safety Stock = Z-score(0.95) × σ_demand × √(lead_time)
```
- Adapts to demand changes automatically
- Considers supplier lead time
- Targets 95% service level

### 4. Predictive Risk Assessment
- Days until stockout calculation
- Stockout probability estimation
- Risk levels: Critical / High / Medium / Low

### 5. Baseline Comparison (Critical for Evaluation)
Side-by-side simulation: Fixed threshold vs StockPilot adaptive strategy

---

## 📈 Proven Results

**Simulation: 60-day demand spike scenario**

| Metric | Fixed Threshold | StockPilot | Improvement |
|--------|----------------|------------|-------------|
| **Stockouts** | 3 | 0 | **100%** ✅ |
| **Service Level** | 96.54% | 100% | **+3.46%** ✅ |
| **Emergency Orders** | 4 | 4 | 0% |
| **Orders Placed** | 7 | 7 | Same efficiency |

**Key insight:** StockPilot eliminates stockouts during demand spikes while maintaining similar order frequency.

---

## 🛠️ Technology Stack

### Backend
- **Python 3.10+** with FastAPI
- **PostgreSQL** for data persistence
- **Pandas + NumPy** for analytics
- **Scikit-learn** for pattern detection

### Frontend
- **React 18** with TypeScript
- **Vite** build tool
- **Material-UI** components
- **Recharts** for visualization

### Automation
- **n8n** for workflow orchestration
- **MCP** integration layer
- **Ollama (Qwen 3 8B)** for assistant explanations
- **Gemini** fallback provider

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (running)
- Node.js 18+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database & generate data
python -c "from models.database import init_db; init_db()"
python -m data.synthetic_generator

# Start API server
uvicorn api.main:app --reload
```

API runs at: `http://localhost:8000`  
Documentation: `http://localhost:8000/api/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## 📊 Dataset

**Synthetic data:** 90 days of inventory history for 6 SKUs with distinct patterns:

1. **SKU-001 (Office Chair):** Stable demand (50±3 units/day)
2. **SKU-002 (Laptop Stand):** Increasing trend (+2% growth/day)
3. **SKU-003 (Desk Lamp):** Weekly seasonality (+50% peaks)
4. **SKU-004 (Wireless Mouse):** Demand spike (20→50 units/day) ⚠️ **Demo SKU**
5. **SKU-005 (Monitor Stand):** Decreasing trend (-1.5%/day)
6. **SKU-006 (USB Cable Pack):** High volatility (40±15 units/day)

**Total:** 540 sales records across 90 days

---

## 🎯 API Endpoints

### Inventory
- `GET /api/inventory` - List all SKUs with current stock
- `GET /api/inventory/{sku_id}` - Get SKU details
- `GET /api/sales-history/{sku_id}` - Get sales history

### Analysis
- `POST /api/analysis/{sku_id}/pattern` - Demand pattern analysis
- `POST /api/analysis/{sku_id}/forecast` - Generate forecast
- `POST /api/analysis/{sku_id}/reorder-point` - Calculate dynamic ROP
- `POST /api/analysis/{sku_id}/risk` - Assess stockout/overstock risk
- `POST /api/analysis/{sku_id}/complete` - Complete analysis

### Simulation
- `POST /api/simulation/run/{sku_id}` - Run baseline comparison
- `GET /api/simulation/comparison` - Compare all SKUs

---

## 🧪 Testing the System

### Test 1: View Inventory
```bash
curl http://localhost:8000/api/inventory
```

### Test 2: Analyze Demo SKU (Demand Spike)
```bash
curl -X POST http://localhost:8000/api/analysis/SKU-004/complete
```

### Test 3: Run Simulation Comparison
```bash
curl -X POST http://localhost:8000/api/simulation/run/SKU-004
```

### Test 4: Risk Assessment
```bash
curl -X POST http://localhost:8000/api/analysis/SKU-004/risk
```

---

## 🔒 Human-in-the-Loop

StockPilot is an **automation assistant**, not an autonomous system.

**What it does:**
- ✅ Analyze patterns
- ✅ Predict risks
- ✅ Recommend actions
- ✅ Generate PO drafts

**What it doesn't do:**
- ❌ Execute purchases without approval
- ❌ Override human decisions
- ❌ Hide reasoning

**All procurement actions require human approval.**

---

## 📐 Evaluation Criteria Alignment

### ✅ Pattern-Learning Quality
- Trend detection via linear regression (R² scoring)
- Seasonality via autocorrelation (7-day period)
- Volatility via coefficient of variation

### ✅ Quantified Improvement
- Direct comparison: same data, both strategies
- Simulation-based: 60-day scenarios
- Metrics: stockouts, service level, inventory levels

### ✅ Realistic Lead-Time Handling
- Supplier lead times: 3-14 days range
- Forecast covers lead time + buffer
- Dynamic ROP = Expected demand during lead time + Safety stock
- Risk assessment: "Days until stockout" vs lead time

### 🌟 Bonus: Supplier Selection
- Multi-supplier database
- Cost vs lead-time trade-offs
- Primary supplier logic
- Extensible for optimization

---

## 🎬 Demo Scenario

**Product:** SKU-004 (Wireless Mouse)  
**Scenario:** Demand spike from 20 → 50 units/day

### Fixed Threshold System:
- Reorder point: 100 units (static)
- Reacts only when stock drops below 100
- **Result:** 3 stockouts ❌

### StockPilot:
- Detects 27% demand increase
- Forecasts continued growth
- Calculates dynamic ROP: 378 units
- Predicts stockout in 3.9 days (lead time is 7 days!)
- Generates PO for 950 units BEFORE stockout
- **Result:** 0 stockouts ✅

---

## 🏆 Why StockPilot Wins

1. **Proactive, not reactive** - Prevents problems before they occur
2. **Pattern-aware** - Learns from actual demand behavior
3. **Explainable** - Every decision has mathematical reasoning
4. **Proven improvement** - Quantified via simulation
5. **Human-controlled** - Automation with accountability
6. **Production-ready architecture** - Agent/Skill/Tool/MCP pattern

---

## 📝 Project Structure

```
stockpilot/
├── backend/
│   ├── agents/          # Decision orchestration
│   ├── skills/          # Business capabilities
│   ├── tools/           # Typed operations
│   ├── workflows/       # n8n integration
│   ├── mcp/             # External system boundary
│   ├── models/          # Database models
│   ├── analytics/       # Pattern/forecast/risk engines
│   ├── simulation/      # Baseline comparison
│   ├── api/             # FastAPI routes
│   ├── assistant/       # LLM assistant (optional)
│   └── data/            # Synthetic data generator
└── frontend/
    └── src/
        ├── components/
        ├── pages/
        └── services/
```

---

## 🔮 Future Roadmap

- Multi-warehouse optimization
- Supplier performance tracking
- Cost optimization algorithms
- Mobile app for approvals
- ERP system integration (SAP, Oracle)
- Advanced seasonality modeling
- Predictive supplier risk management
- Carbon footprint optimization

---

## 👥 Team

**Built for Hack the Horizon 2.0**

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- FastAPI for excellent Python web framework
- Material-UI for React components
- Recharts for data visualization
- n8n for workflow automation
- Ollama for local LLM inference

---

**Built with ❤️ for Smart Automation**

*StockPilot: Predict. Replenish. Automate.*
