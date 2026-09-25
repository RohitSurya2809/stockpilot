# n8n Workflows - Location Guide

**Build:** ✅ Success (1.55s)  
**All 3 workflows now accessible**

---

## Workflow Overview

| # | Name | Trigger Type | Location | Endpoint |
|---|------|--------------|----------|----------|
| **1** | PO Approval | Manual Button | Analysis page | `/procurement/auto-generate/{sku_id}` |
| **2** | Critical Alert | Auto-trigger | Analysis page (hidden) | n8n webhook |
| **3** | Check All Reorder | Manual Button | Dashboard header | `/n8n/check-reorder` |

---

## Workflow 1: PO Approval Flow

### Location
**Analysis Page** → After running analysis → "Auto-Generate Purchase Order" button

### When It Shows
- Only visible when `needs_reorder === true`
- Located in "Agent Decision" section at bottom

### What It Does
1. Creates PO in backend database
2. Fires n8n webhook: `stockpilot-po-approval`
3. n8n workflow handles approval flow (email/Slack notification)

### Button Label
```
Auto-Generate Purchase Order
```

### API Flow
```
POST /api/procurement/auto-generate/SKU-004
  → Creates PO in database
  → Returns PO details

POST https://saravanan2007.app.n8n.cloud/webhook/stockpilot-po-approval
  → Triggers n8n approval workflow
  → Fire-and-forget (doesn't wait for response)
```

---

## Workflow 2: Critical Alert

### Location
**Analysis Page** → Auto-triggers when risk = critical (no visible button)

### When It Triggers
Automatically when analysis shows:
```typescript
risk_assessment.risk_level === 'critical'
```

### What It Does
1. Sends webhook to n8n with:
   - SKU ID
   - Current stock level
   - Risk level (critical)
   - Reason/message
   - Timestamp

2. n8n workflow handles:
   - Slack alert to ops team
   - Email to procurement manager
   - SMS to on-call person (if configured)

### No User Action Required
This is **fire-and-forget** - happens automatically in background.

User sees: Normal analysis results  
Behind the scenes: Critical alert webhook sent

### API Flow
```
Analysis detects: risk_level === 'critical'
  ↓
POST https://saravanan2007.app.n8n.cloud/webhook/stockpilot-critical-alert
{
  "sku_id": "SKU-004",
  "current_stock": 0,
  "risk_level": "critical",
  "message": "Already in stockout condition. Immediate action required.",
  "timestamp": "2026-09-25T07:30:00.000Z"
}
  ↓
n8n sends alerts to team
```

---

## Workflow 3: Check All for Reorder

### Location
**Dashboard Page** → Top right header → "Check All for Reorder" button

### Button Label
```
Check All for Reorder
```

### What It Does
1. Analyzes **all SKUs** in inventory (batch operation)
2. Identifies which ones need reordering
3. Returns summary:
   - Total SKUs checked
   - Number that need reorder
   - List of alerts

4. Shows result banner:
   ```
   Checked 6 SKUs - 1 need reorder
   ```

5. Reloads inventory to show updated status

### API Flow
```
GET /api/n8n/check-reorder
  → Runs ProcurementWorkflow.analyze_all_skus()
  → Returns:
  {
    "timestamp": "2026-09-25",
    "total_skus_checked": 6,
    "reorder_needed": 1,
    "alerts": [
      {
        "sku_id": "SKU-004",
        "risk_level": "critical",
        "reasoning": "...",
        "needs_reorder": true,
        "recommended_order": {...}
      }
    ]
  }
```

### Use Case
- Run at end of day to check all inventory
- Scheduled (e.g., hourly via n8n cron)
- Manual trigger when needed

---

## Visual Guide

### Dashboard
```
┌─────────────────────────────────────────────────┐
│ Inventory Intelligence    [Check All for Reorder] │ ← Workflow 3
│ Real-time demand forecasting                     │
├─────────────────────────────────────────────────┤
│ Checked 6 SKUs - 1 need reorder                  │ ← Result shows here
│                                                   │
│ [6 SKUs] [1 At Risk] [6 Below ROP]              │
│                                                   │
│ SKU-004 - Wireless Mouse                         │
│ Current Stock: 0 units                           │
│ Forecast: 61.3/day (blue)                        │
│ Risk: CRITICAL (red)                             │
│ [Run Analysis]                                   │
└─────────────────────────────────────────────────┘
```

### Analysis Page
```
┌─────────────────────────────────────────────────┐
│ SKU Analysis                                     │
│                                                   │
│ [SKU-004]  [Run Analysis]                       │
│                                                   │
│ AGENT DECISION                                   │
│ ⚠ IMMEDIATE REORDER                             │
│ Reason: Already in stockout condition            │
│ Skills: Demand Analysis, Risk Assessment         │
│                                                   │
│ [Auto-Generate Purchase Order]  ← Workflow 1     │
│ PO PO-20260925-001 created - 1200 units, $30000 │
└─────────────────────────────────────────────────┘

Workflow 2 triggered automatically (no button)
```

---

## Testing Each Workflow

### Test Workflow 1
1. Go to Dashboard
2. Click "Run Analysis" on SKU-004 (currently has 0 stock)
3. Analysis shows: ⚠ IMMEDIATE REORDER
4. Click "Auto-Generate Purchase Order"
5. Should see: `PO PO-xxx created - 1200 units, $30000`
6. Check n8n: Webhook should receive PO data

### Test Workflow 2
1. Go to Dashboard
2. Click "Run Analysis" on SKU-004 (critical risk)
3. Analysis completes normally
4. Check browser DevTools → Network tab
5. Should see POST to: `stockpilot-critical-alert` (may show as failed if n8n not configured)
6. Check n8n: Webhook should receive alert data

**Note:** Alert sends even if analysis page looks normal - it's fire-and-forget in background.

### Test Workflow 3
1. Go to Dashboard
2. Click "Check All for Reorder" (top right)
3. Button shows "Checking..."
4. After ~2 seconds, see: "Checked 6 SKUs - X need reorder"
5. Dashboard reloads automatically
6. Check backend logs: Should see analysis running for all SKUs

---

## n8n Webhook URLs

```
Workflow 1 (PO Approval):
POST https://saravanan2007.app.n8n.cloud/webhook/stockpilot-po-approval

Workflow 2 (Critical Alert):
POST https://saravanan2007.app.n8n.cloud/webhook/stockpilot-critical-alert

Workflow 3 (Check Reorder):
Calls backend API, backend can optionally webhook n8n for email alerts
```

---

## Backend API Endpoints

```
# Workflow 1: Generate PO
POST /api/procurement/auto-generate/{sku_id}?created_by=n8n_workflow

# Workflow 2: No direct endpoint (webhook from frontend)
# Fire-and-forget to n8n

# Workflow 3: Check all SKUs
GET /api/n8n/check-reorder
```

---

## For Judge Demo

### Show Workflow 1
"This button auto-generates a purchase order and sends it through our n8n approval flow. The PO is created in our database, and n8n handles the approval workflow with email and Slack notifications."

### Explain Workflow 2
"When the system detects a critical risk, it automatically fires a webhook to n8n that alerts our operations team via Slack and email. This happens behind the scenes - no manual action needed."

### Demo Workflow 3
"This button checks all 6 SKUs at once and tells us which ones need reordering. In production, this runs on a schedule every hour via n8n."

---

## Summary

**Workflow 1:** ✅ Button in Analysis page (visible when reorder needed)  
**Workflow 2:** ✅ Auto-triggers when risk is critical (invisible to user)  
**Workflow 3:** ✅ Button in Dashboard header (check all SKUs)

**All 3 workflows now accessible in the UI!**
