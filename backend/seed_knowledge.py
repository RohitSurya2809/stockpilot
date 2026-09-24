"""Seed the knowledge base with StockPilot domain knowledge for RAG."""

from models import get_db, KnowledgeBase

KNOWLEDGE = [
    ("definition", "reorder point", "The Reorder Point (ROP) is the inventory level that triggers a new purchase order. StockPilot uses a dynamic ROP that adapts to changing demand patterns, unlike static thresholds."),
    ("definition", "safety stock", "Safety stock is extra inventory held as a buffer against demand uncertainty and supply delays. StockPilot calculates it using demand variability and supplier lead time."),
    ("definition", "stockout", "A stockout occurs when inventory reaches zero and demand cannot be fulfilled. StockPilot's ML forecasting aims to predict and prevent stockouts before they happen."),
    ("definition", "lead time", "Lead time is the number of days between placing an order and receiving the goods. Longer lead times require earlier reordering and higher safety stock."),
    ("definition", "service level", "Service level is the percentage of demand that can be fulfilled from available stock. StockPilot targets 95-98% service level using dynamic reorder points."),
    ("explanation", "ML forecast", "StockPilot uses a RandomForestRegressor machine learning model that learns from historical sales patterns. It engineers 8 features including lag values, rolling averages, and day-of-week effects. When enough data is available (30+ days), ML provides more accurate forecasts than simple moving averages."),
    ("explanation", "statistical fallback", "When insufficient historical data exists for ML (less than 30 days), StockPilot transparently falls back to statistical methods: moving average + trend adjustment + seasonality. This is honest behavior, not a failure."),
    ("explanation", "risk assessment", "StockPilot assesses stockout risk by comparing current inventory against the dynamic reorder point, considering supplier lead time and demand trends. Risk levels: CRITICAL (stockout imminent), HIGH (below ROP), MEDIUM (approaching ROP), LOW (sufficient stock)."),
    ("explanation", "confidence level", "Forecast confidence indicates how reliable the prediction is. ML forecasts typically show 90-95% confidence based on validation accuracy. Statistical forecasts show lower confidence (40-60%) because they use simpler models."),
    ("process", "purchase order workflow", "When a SKU needs reorder: 1) Analysis detects risk 2) Auto-Generate PO creates order in database 3) n8n workflow sends email and Slack notification 4) Manager reviews and approves/rejects 5) Order is placed with supplier."),
    ("process", "analysis workflow", "To analyze a SKU: Go to Analysis page, enter SKU ID, click Analyze. The system runs pattern analysis, ML forecast, dynamic ROP calculation, and risk assessment. Results show on one page with ML badges."),
    ("faq", "where to see ML metrics", "ML metrics appear on the Analysis page after running an analysis. Look for the blue '🤖 ML: RandomForestRegressor' badge in the Forecast card. Validation MAE and RMSE are shown below."),
    ("faq", "how to create purchase order", "Click the 'Auto-Generate Purchase Order' button on the Analysis page after analyzing a SKU. This creates a PO in the database and notifies the procurement team via email and Slack through n8n."),
    ("faq", "how to check all SKUs", "Click 'Run Reorder Check' on the Dashboard page. This checks all SKUs and shows which ones need reordering."),
    ("faq", "what is simulation", "The Simulation page compares StockPilot's adaptive strategy against a traditional fixed-threshold approach using real historical data. It proves StockPilot reduces stockouts."),
    ("policy", "reorder policy", "StockPilot recommends reordering when: inventory drops below the dynamic reorder point, OR stockout risk is critical. Order quantity covers forecasted demand during lead time plus safety stock buffer."),
]

def seed():
    db = next(get_db())
    existing = db.query(KnowledgeBase).count()
    if existing > 0:
        print(f"Knowledge base already has {existing} entries. Skipping seed.")
        return

    for category, key, content in KNOWLEDGE:
        entry = KnowledgeBase(category=category, key=key, content=content)
        db.add(entry)

    db.commit()
    print(f"Seeded {len(KNOWLEDGE)} knowledge base entries.")

if __name__ == "__main__":
    seed()
