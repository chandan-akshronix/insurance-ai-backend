"""
Quick migration script to add 'role' column
Run this from the backend directory with venv activated
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import text
    from database import SessionLocal
    print("\n🔧 Adding 'role' column to users table...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Check if column exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            print("✅ Column 'role' already exists!")
        else:
            print("Adding 'role' column...")
            # Add column
            alter_query = text("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR(20) DEFAULT 'user'
            """)
            db.execute(alter_query)
            db.commit()
            print("✅ Successfully added 'role' column!")
            
            # Update existing users
            update_query = text("""
                UPDATE users 
                SET role = 'user' 
                WHERE role IS NULL
            """)
            db.execute(update_query)
            db.commit()
            print("✅ Updated existing users to have 'user' role")
        
        print("=" * 60)
        print("✅ Migration completed!\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        print("\n💡 Alternative: Run this SQL directly on your database:")
        print("   ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';")
        sys.exit(1)
    finally:
        db.close()
        
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\n💡 Make sure you:")
    print("   1. Are in the 'Innsurance Backend Fast API' directory")
    print("   2. Have activated the virtual environment (venv)")
    print("   3. Have installed requirements: pip install -r requirements.txt")
    print("\n💡 Or run this SQL directly on Azure PostgreSQL:")
    print("   ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';")
    sys.exit(1)

