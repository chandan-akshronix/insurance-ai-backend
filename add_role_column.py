"""
Migration script to add 'role' column to existing users table
Run this script to update your PostgreSQL database schema
"""
from sqlalchemy import text, inspect
from database import SessionLocal, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_role_column():
    """
    Add 'role' column to users table if it doesn't exist
    """
    db = SessionLocal()
    try:
        logger.info("Checking if 'role' column exists...")
        
        # Check if column exists using information_schema
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            logger.info("✅ Column 'role' already exists in users table")
        else:
            logger.info("Adding 'role' column to users table...")
            
            # Add column with default value
            alter_query = text("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR(20) DEFAULT 'user'
            """)
            db.execute(alter_query)
            db.commit()
            logger.info("✅ Successfully added 'role' column to users table")
            
            # Update existing users to have 'user' role (safety check)
            update_query = text("""
                UPDATE users 
                SET role = 'user' 
                WHERE role IS NULL
            """)
            db.execute(update_query)
            db.commit()
            logger.info("✅ Updated existing users to have 'user' role")
        
        # Verify
        verify_query = text("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """)
        verify_result = db.execute(verify_query).fetchone()
        if verify_result:
            logger.info(f"✅ Verification: Column exists - Type: {verify_result[1]}, Default: {verify_result[2]}")
        
        logger.info("\n✅ Migration completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error adding role column: {str(e)}")
        logger.error("You can also run the SQL manually:")
        logger.error("  ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔧 Database Migration: Adding 'role' Column")
    print("=" * 60)
    try:
        add_role_column()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Alternative: Run the SQL command directly:")
        print("   ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';")
    print("=" * 60)
    print("\n✅ Script completed!\n")
