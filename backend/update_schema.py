"""
Database Schema Update Script

Updates the database schema to reflect model changes.
For Phase 3: Update PurchaseOrder table with new fields.
"""

from sqlalchemy import text
from models.database import engine, init_db, test_connection
from models import Base


def update_schema():
    """
    Update database schema

    WARNING: This drops and recreates tables!
    In production, use proper migrations (Alembic)
    """
    print("=" * 70)
    print("DATABASE SCHEMA UPDATE")
    print("=" * 70)
    print()

    # Test connection
    print("Step 1: Testing database connection...")
    if not test_connection():
        print("[ERROR] Database connection failed!")
        return
    print("[OK] Database connected")
    print()

    # Drop and recreate purchase_orders table
    print("Step 2: Updating purchase_orders table...")
    try:
        with engine.begin() as conn:
            # Drop table
            conn.execute(text("DROP TABLE IF EXISTS purchase_orders CASCADE"))
            print("[OK] Dropped existing purchase_orders table")

            # Recreate with new schema
            # This will create the table using the current model definition
            Base.metadata.tables['purchase_orders'].create(conn)
            print("[OK] Created purchase_orders table with new schema")
    except Exception as e:
        print(f"[ERROR] Schema update failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 70)
    print("SCHEMA UPDATE COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Synthetic data is still intact (skus, inventory, sales_history)")
    print("  2. Purchase orders table is now ready for Phase 3")
    print("  3. Run: python -m workflows.procurement_workflow")
    print()


if __name__ == "__main__":
    update_schema()
