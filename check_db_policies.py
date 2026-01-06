"""
Database Check Script for Policies
Uses backend's existing database setup
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from database import SessionLocal, engine
    from models import Policy, User
    from sqlalchemy import func, text
    
    def check_database():
        """Check database for policies and users"""
        db = SessionLocal()
        
        try:
            print("=" * 80)
            print("DATABASE POLICY CHECK")
            print("=" * 80)
            print()
            
            # Check total users
            user_count = db.query(func.count(User.id)).scalar()
            print(f"[INFO] Total Users in Database: {user_count}")
            print()
            
            # Check total policies
            policy_count = db.query(func.count(Policy.id)).scalar()
            print(f"[INFO] Total Policies in Database: {policy_count}")
            print()
            
            # Check users with policies
            result = db.execute(text("""
                SELECT DISTINCT u.id, u.name, u.email, COUNT(p.id) as policy_count
                FROM users u
                LEFT JOIN policy p ON u.id = p."userId"
                GROUP BY u.id, u.name, u.email
                ORDER BY policy_count DESC
                LIMIT 10
            """))
            
            users_with_policies = result.fetchall()
            print("[INFO] Users and Their Policy Counts:")
            print("-" * 80)
            print(f"{'User ID':<10} {'Name':<30} {'Email':<35} {'Policy Count':<15}")
            print("-" * 80)
            
            for row in users_with_policies:
                user_id, name, email, policy_count = row
                print(f"{user_id:<10} {str(name)[:28]:<30} {str(email)[:33]:<35} {policy_count:<15}")
            
            print()
            
            # Get sample policies with details
            result = db.execute(text("""
                SELECT 
                    p.id,
                    p."userId",
                    p.type,
                    p."planName",
                    p."policyNumber",
                    p.coverage,
                    p.premium,
                    p.status,
                    p."startDate",
                    p."expiryDate",
                    u.name as user_name,
                    u.email as user_email
                FROM policy p
                LEFT JOIN users u ON p."userId" = u.id
                ORDER BY p.id
                LIMIT 10
            """))
            
            policies = result.fetchall()
            print("[INFO] Sample Policies (First 10):")
            print("-" * 80)
            
            if policies:
                for policy in policies:
                    (p_id, user_id, p_type, plan_name, policy_number, coverage, 
                     premium, status, start_date, expiry_date, user_name, user_email) = policy
                    
                    print(f"Policy ID: {p_id}")
                    print(f"  User ID: {user_id} ({user_name or 'N/A'} - {user_email or 'N/A'})")
                    print(f"  Type: {p_type}")
                    print(f"  Plan Name: {plan_name}")
                    print(f"  Policy Number: {policy_number}")
                    print(f"  Coverage: Rs {coverage:,.2f}" if coverage else "  Coverage: None")
                    print(f"  Premium: Rs {premium:,.2f}" if premium else "  Premium: None")
                    print(f"  Status: {status or 'None'}")
                    print(f"  Start Date: {start_date}")
                    print(f"  Expiry Date: {expiry_date}")
                    print("-" * 80)
            else:
                print("[WARN] No policies found in database")
            
            print()
            
            # Check for policies with missing required fields
            result = db.execute(text("""
                SELECT COUNT(*) as count
                FROM policy
                WHERE status IS NULL OR status = ''
            """))
            null_status_count = result.scalar()
            
            result = db.execute(text("""
                SELECT COUNT(*) as count
                FROM policy
                WHERE coverage IS NULL OR premium IS NULL
            """))
            null_values_count = result.scalar()
            
            print("[WARN] Data Quality Checks:")
            print(f"  Policies with NULL/empty status: {null_status_count}")
            print(f"  Policies with NULL coverage/premium: {null_values_count}")
            print()
            
            # Check policy types distribution
            result = db.execute(text("""
                SELECT type, COUNT(*) as count
                FROM policy
                GROUP BY type
                ORDER BY count DESC
            """))
            
            type_distribution = result.fetchall()
            print("[INFO] Policy Type Distribution:")
            if type_distribution:
                for p_type, count in type_distribution:
                    print(f"  {p_type}: {count}")
            else:
                print("  No policies found")
            print()
            
            # Check status distribution
            result = db.execute(text("""
                SELECT status, COUNT(*) as count
                FROM policy
                WHERE status IS NOT NULL AND status != ''
                GROUP BY status
                ORDER BY count DESC
            """))
            
            status_distribution = result.fetchall()
            print("[INFO] Status Distribution:")
            if status_distribution:
                for status, count in status_distribution:
                    print(f"  {status}: {count}")
            else:
                print("  No policies with status found")
            print()
            
            # Check policies by user ID (for common user IDs)
            print("[INFO] Policies by User ID:")
            result = db.execute(text("""
                SELECT "userId", COUNT(*) as count
                FROM policy
                GROUP BY "userId"
                ORDER BY count DESC
                LIMIT 5
            """))
            
            policies_by_user = result.fetchall()
            if policies_by_user:
                for user_id, count in policies_by_user:
                    print(f"  User ID {user_id}: {count} policies")
            else:
                print("  No policies found")
            print()
            
            db.close()
            
            print("=" * 80)
            print("[SUCCESS] Database Check Complete")
            print("=" * 80)
            
            return {
                'user_count': user_count,
                'policy_count': policy_count,
                'users_with_policies': len([u for u in users_with_policies if u[3] > 0]),
                'policies': policies
            }
            
        except Exception as e:
            print(f"[ERROR] Error checking database: {str(e)}")
            import traceback
            traceback.print_exc()
            db.close()
            return None
    
    if __name__ == "__main__":
        check_database()
        
except ImportError as e:
    print("ERROR: Error importing modules:")
    print(f"   {str(e)}")
    print()
    print("Please make sure you're running from the insurance-ai-backend directory")
    print("and that all dependencies are installed:")
    print("   pip install -r requirements.txt")

