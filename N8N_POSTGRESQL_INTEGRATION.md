# n8n PostgreSQL Integration Guide

**Status:** Phase F-G - Documentation for Future Implementation  
**Date:** 2026-09-24

---

## Overview

This document outlines the requirements for integrating n8n workflows with the StockPilot PostgreSQL database, replacing the previous Google Sheets-based approach.

---

## Current State

**Finding:** No n8n workflow files found in the repository.

**Assumption:** n8n workflows may be:
1. Stored in n8n cloud/instance (not in repo)
2. Not yet implemented
3. Planned for future implementation

---

## Required n8n Workflows

Based on the StockPilot architecture, the following workflows should be created:

### Workflow 1: Daily Inventory Sync
**Purpose:** Sync inventory data from external sources to PostgreSQL

**Nodes Required:**
1. **Trigger Node:** Schedule Trigger (daily at configured time)
2. **Data Source:** 
   - HTTP Request node (if pulling from external API)
   - OR FTP node (if receiving files)
   - OR Email node (if receiving attachments)
3. **Transform Node:** Code node or Function node to parse and validate data
4. **PostgreSQL Node:** Insert/Update operations
   - Table: `inventory`
   - Fields: `sku_id`, `current_stock`, `safety_stock`, `reorder_point`
5. **Error Handler:** Send notification if sync fails

**Migration from Google Sheets:**
- Replace "Google Sheets" node with "PostgreSQL" node
- Update connection credentials
- Modify queries from sheets API to SQL:
  ```sql
  INSERT INTO inventory (sku_id, current_stock, updated_at)
  VALUES ($1, $2, NOW())
  ON CONFLICT (sku_id) 
  DO UPDATE SET current_stock = EXCLUDED.current_stock, updated_at = NOW();
  ```

---

### Workflow 2: Sales Data Import
**Purpose:** Import daily sales transactions into PostgreSQL

**Nodes Required:**
1. **Trigger Node:** Webhook (for real-time) or Schedule (for batch)
2. **Data Validation:** Code node to validate sales data format
3. **PostgreSQL Node:** Bulk insert into `sales_history`
   ```sql
   INSERT INTO sales_history (sku_id, date, quantity_sold, created_at)
   VALUES ($1, $2, $3, NOW())
   ON CONFLICT (sku_id, date) 
   DO UPDATE SET quantity_sold = sales_history.quantity_sold + EXCLUDED.quantity_sold;
   ```
4. **Analytics Trigger:** HTTP Request to StockPilot API to recalculate metrics
5. **Notification Node:** Slack/Email notification on completion

**Migration from Google Sheets:**
- Change from reading Google Sheets to direct database insert
- Remove Google Sheets authentication
- Add PostgreSQL connection with credentials from `.env`

---

### Workflow 3: Automated Reorder Alerts
**Purpose:** Monitor inventory levels and trigger reorder alerts

**Nodes Required:**
1. **Trigger Node:** Schedule Trigger (every hour)
2. **PostgreSQL Query Node:** 
   ```sql
   SELECT 
     s.id as sku_id,
     s.name as product_name,
     i.current_stock,
     i.reorder_point,
     sup.name as supplier_name,
     sup.email as supplier_email
   FROM skus s
   JOIN inventory i ON s.id = i.sku_id
   JOIN sku_suppliers ss ON s.id = ss.sku_id AND ss.is_primary = true
   JOIN suppliers sup ON ss.supplier_id = sup.id
   WHERE i.current_stock < i.reorder_point
     AND i.updated_at > NOW() - INTERVAL '24 hours';
   ```
3. **Decision Node (IF):** Check if results exist
4. **StockPilot API Call:** POST to `/api/procurement/analyze/{sku_id}` for each SKU
5. **Generate PO:** POST to `/api/procurement/auto-generate/{sku_id}`
6. **Notification Nodes:**
   - Email to procurement team
   - Slack message to #procurement channel
   - Optional: SMS for critical items

**Migration from Google Sheets:**
- Replace Google Sheets lookup with SQL query
- Update email templates to use SQL results instead of sheet data
- Add integration with StockPilot procurement API

---

## PostgreSQL Connection Setup

### n8n Credential Configuration

1. **Create PostgreSQL Credential in n8n:**
   - Name: `StockPilot Production DB`
   - Host: `localhost` (or production host)
   - Database: `stockpilot`
   - User: `stockpilot_user`
   - Password: (from environment variable)
   - Port: `5432`
   - SSL: `require` (for production)

2. **Environment Variables:**
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_DB=stockpilot
   POSTGRES_USER=stockpilot_user
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_PORT=5432
   ```

3. **Connection String Format:**
   ```
   postgresql://stockpilot_user:password@localhost:5432/stockpilot?sslmode=require
   ```

---

## Migration Checklist

### Phase 1: Setup (1-2 hours)
- [ ] Install n8n (if not already installed)
- [ ] Configure PostgreSQL credentials in n8n
- [ ] Test database connection
- [ ] Create backup of existing Google Sheets data

### Phase 2: Workflow 1 - Inventory Sync (2-3 hours)
- [ ] Create new n8n workflow
- [ ] Add schedule trigger
- [ ] Replace Google Sheets read with PostgreSQL query
- [ ] Replace Google Sheets write with PostgreSQL insert/update
- [ ] Test with sample data
- [ ] Add error handling
- [ ] Deploy and monitor for 24 hours

### Phase 3: Workflow 2 - Sales Import (2-3 hours)
- [ ] Create sales data import workflow
- [ ] Configure webhook or schedule trigger
- [ ] Add data validation logic
- [ ] Replace Google Sheets append with PostgreSQL insert
- [ ] Test bulk insert performance
- [ ] Add API trigger to recalculate metrics
- [ ] Deploy and verify

### Phase 4: Workflow 3 - Reorder Alerts (3-4 hours)
- [ ] Create reorder monitoring workflow
- [ ] Write SQL query for items below ROP
- [ ] Integrate with StockPilot procurement API
- [ ] Configure email/Slack notifications
- [ ] Test alert generation
- [ ] Verify PO auto-generation
- [ ] Deploy to production

### Phase 5: Validation & Cleanup (1-2 hours)
- [ ] Run all workflows end-to-end
- [ ] Compare results with Google Sheets (if still running)
- [ ] Monitor for 1 week in parallel
- [ ] Deprecate Google Sheets workflows
- [ ] Document final workflows
- [ ] Train team on new system

---

## Integration with StockPilot API

All n8n workflows should leverage the StockPilot FastAPI backend:

### Key Endpoints for n8n:

1. **Analyze SKU:**
   ```
   POST /api/procurement/analyze/{sku_id}
   Response: Full analysis with ML forecast, ROP, risk assessment
   ```

2. **Auto-generate PO:**
   ```
   POST /api/procurement/auto-generate/{sku_id}?created_by=n8n_workflow
   Response: Purchase order details
   ```

3. **Get Pending Approvals:**
   ```
   GET /api/procurement/pending-approvals
   Response: List of POs awaiting approval
   ```

4. **Inventory Status:**
   ```
   GET /api/inventory
   Response: All SKUs with current stock levels
   ```

---

## Benefits of PostgreSQL vs Google Sheets

| Feature | Google Sheets | PostgreSQL |
|---------|---------------|------------|
| **Data Integrity** | Manual, prone to errors | ACID compliant, constraints enforced |
| **Performance** | Slow for large datasets | Fast queries, indexed |
| **Concurrency** | Limited simultaneous users | Unlimited connections |
| **ML Integration** | Requires export/import | Direct Python access |
| **Version Control** | Manual snapshots | Transaction logs, backups |
| **Security** | Sheet-level permissions | Row-level security, encryption |
| **Scalability** | Limited to ~5M cells | Unlimited rows |
| **API Access** | Rate limited | Direct SQL access |

---

## Sample n8n Workflow JSON Structure

```json
{
  "name": "StockPilot - Daily Inventory Sync",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "triggerAtHour": 2
            }
          ]
        }
      },
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger"
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT sku_id, current_stock FROM inventory WHERE updated_at > NOW() - INTERVAL '1 day'"
      },
      "name": "Get Updated Inventory",
      "type": "n8n-nodes-base.postgres"
    },
    {
      "parameters": {
        "functionCode": "// Process and validate data\nreturn items.map(item => ({\n  sku_id: item.json.sku_id,\n  stock: item.json.current_stock,\n  timestamp: new Date().toISOString()\n}));"
      },
      "name": "Transform Data",
      "type": "n8n-nodes-base.function"
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{ "node": "Get Updated Inventory", "type": "main", "index": 0 }]]
    },
    "Get Updated Inventory": {
      "main": [[{ "node": "Transform Data", "type": "main", "index": 0 }]]
    }
  }
}
```

---

## Testing Strategy

### Unit Tests:
- Test each node individually with mock data
- Verify SQL queries return expected results
- Validate data transformations

### Integration Tests:
- Run full workflow end-to-end
- Verify database updates
- Check API calls succeed
- Confirm notifications sent

### Load Tests:
- Test with 1000+ SKU records
- Measure query performance
- Check bulk insert speed
- Monitor memory usage

---

## Rollback Plan

If PostgreSQL migration fails:

1. **Immediate:** Keep Google Sheets workflows active in parallel for 1 week
2. **Fallback:** Document process to revert to sheets-based approach
3. **Data Recovery:** Daily PostgreSQL backups for 30 days
4. **Monitoring:** Alert if any workflow fails 2+ times in 24 hours

---

## Next Steps

1. **Determine if n8n is already deployed:**
   - Check with team for existing n8n instance
   - If not, decide: Cloud vs Self-hosted

2. **Create workflows:**
   - Start with Workflow 1 (lowest risk)
   - Test thoroughly before moving to Workflow 2 & 3

3. **Documentation:**
   - Record all workflow IDs
   - Document trigger schedules
   - Create runbook for common issues

4. **Training:**
   - Train procurement team on new alerts
   - Document how to manually trigger workflows
   - Create troubleshooting guide

---

## Status: Ready for Implementation

All requirements documented. Implementation can begin when n8n instance is available.

**Estimated Total Time:** 8-15 hours (depending on n8n familiarity)
