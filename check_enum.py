"""Check database enum values"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check enum definition
    result = db.execute(text("""
        SELECT t.typname, e.enumlabel 
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid 
        WHERE t.typname = 'policytype' 
        ORDER BY e.enumsortorder
    """))
    enum_values = result.fetchall()
    print("Database enum 'policytype' values:")
    for row in enum_values:
        print(f"  {row[1]}")
    
    # Check current policy types
    result = db.execute(text("SELECT DISTINCT type FROM policy LIMIT 5"))
    current_types = [row[0] for row in result.fetchall()]
    print("\nCurrent policy types in database:")
    for t in current_types:
        print(f"  {t}")
finally:
    db.close()

