"""
Fix Policy Status and Type Script
Updates all policies to have status and correct type enum values
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionLocal
    from models import Policy
    from sqlalchemy import text
    
    def fix_policies():
        """Fix policy status and type issues"""
        db = SessionLocal()
        
        try:
            print("=" * 80)
            print("FIXING POLICY STATUS AND TYPE")
            print("=" * 80)
            print()
            
            # Fix 1: Update NULL statuses to 'Active'
            print("[FIX 1] Updating NULL statuses to 'Active'...")
            result = db.execute(text("""
                UPDATE policy 
                SET status = 'Active' 
                WHERE status IS NULL OR status = ''
            """))
            db.commit()
            updated_count = result.rowcount
            print(f"[SUCCESS] Updated {updated_count} policies with status = 'Active'")
            print()
            
            # Fix 2: Update policy types to use enum values
            print("[FIX 2] Updating policy types to enum values...")
            result = db.execute(text("""
                UPDATE policy 
                SET type = 'life_insurance' 
                WHERE type = 'life'
            """))
            db.commit()
            type_updated = result.rowcount
            print(f"[SUCCESS] Updated {type_updated} policies with type = 'life_insurance'")
            print()
            
            # Verify fixes
            print("[VERIFY] Verifying fixes...")
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status IS NOT NULL AND status != '' THEN 1 END) as with_status,
                    COUNT(CASE WHEN type = 'life_insurance' THEN 1 END) as with_correct_type
                FROM policy
            """))
            stats = result.fetchone()
            total, with_status, with_correct_type = stats
            
            print(f"  Total policies: {total}")
            print(f"  Policies with status: {with_status}")
            print(f"  Policies with correct type: {with_correct_type}")
            print()
            
            # Show status distribution
            result = db.execute(text("""
                SELECT status, COUNT(*) as count
                FROM policy
                GROUP BY status
                ORDER BY count DESC
            """))
            status_dist = result.fetchall()
            print("[INFO] Status Distribution:")
            for status, count in status_dist:
                print(f"  {status}: {count}")
            print()
            
            # Show type distribution
            result = db.execute(text("""
                SELECT type, COUNT(*) as count
                FROM policy
                GROUP BY type
                ORDER BY count DESC
            """))
            type_dist = result.fetchall()
            print("[INFO] Type Distribution:")
            for p_type, count in type_dist:
                print(f"  {p_type}: {count}")
            print()
            
            db.close()
            
            print("=" * 80)
            print("[SUCCESS] Policy fixes complete!")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error fixing policies: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            db.close()
            return False
    
    if __name__ == "__main__":
        print()
        response = input("This will update all policies. Continue? (yes/no): ").strip().lower()
        if response == 'yes':
            fix_policies()
        else:
            print("Cancelled.")

except ImportError as e:
    print("[ERROR] Error importing modules:")
    print(f"   {str(e)}")
    print()
    print("Please make sure you're running from the insurance-ai-backend directory")
    print("and that all dependencies are installed:")
    print("   pip install -r requirements.txt")

