"""
Verify that claim documents are saved in MongoDB with proper structure
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def verify_claim_documents_in_mongodb():
    """Verify claim documents are in MongoDB with proper structure"""
    print("=" * 70)
    print("TASK 7: VERIFY CLAIM DOCUMENTS IN MONGODB")
    print("=" * 70)
    
    backend_dir = Path(__file__).parent
    env_file = backend_dir / ".env"
    
    if not env_file.exists():
        print("\n❌ .env file not found")
        return False
    
    load_dotenv(env_file)
    
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "insurance_db")
    
    if not mongo_uri:
        print("\n❌ MONGODB_URI not set in .env")
        return False
    
    try:
        print(f"\n🔄 Connecting to MongoDB...")
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        coll = db['claims']
        
        print(f"✅ Connected to database: {db_name}, collection: claims")
        
        # Get all claims with documents
        print(f"\n📋 Checking for claim documents in MongoDB...")
        cursor = coll.find({'documents': {'$exists': True, '$ne': []}})
        claims_with_docs = await cursor.to_list(length=100)
        
        if claims_with_docs:
            print(f"\n✅ Found {len(claims_with_docs)} claim(s) with documents")
            
            # Verify document structure
            print(f"\n📊 Document Structure Verification:")
            print("-" * 70)
            
            required_fields = ['filename', 'url', 'docType', 'category']
            optional_fields = ['documentId']
            
            all_valid = True
            for claim_idx, claim in enumerate(claims_with_docs[:5]):  # Check first 5
                claim_id = claim.get('_id', 'N/A')
                documents = claim.get('documents', [])
                
                print(f"\n  Claim ID: {claim_id}")
                print(f"    Documents: {len(documents)}")
                
                for doc_idx, doc in enumerate(documents):
                    print(f"\n    Document {doc_idx + 1}:")
                    
                    # Check required fields
                    missing_required = [field for field in required_fields if not doc.get(field)]
                    if missing_required:
                        print(f"      ❌ Missing required fields: {missing_required}")
                        all_valid = False
                    else:
                        print(f"      ✅ All required fields present")
                    
                    # Display field values
                    for field in required_fields + optional_fields:
                        value = doc.get(field, 'N/A')
                        if field == 'url' and value != 'N/A':
                            # Truncate URL for display
                            display_value = value[:80] + '...' if len(value) > 80 else value
                            is_azure = 'blob.core.windows.net' in value
                            print(f"      - {field}: {display_value} {'✅ Azure' if is_azure else '⚠️  Not Azure'}")
                        else:
                            print(f"      - {field}: {value}")
            
            if all_valid:
                print(f"\n✅ All documents have proper structure")
            else:
                print(f"\n⚠️  Some documents are missing required fields")
            
            # Check Azure URLs
            print(f"\n🔗 Azure URL Verification:")
            print("-" * 70)
            total_docs = sum(len(c.get('documents', [])) for c in claims_with_docs)
            azure_docs = 0
            
            for claim in claims_with_docs:
                for doc in claim.get('documents', []):
                    url = doc.get('url', '')
                    if url and 'blob.core.windows.net' in url:
                        azure_docs += 1
            
            print(f"✅ Total documents: {total_docs}")
            print(f"✅ Documents with Azure URLs: {azure_docs}")
            print(f"✅ Azure URL coverage: {(azure_docs/total_docs*100) if total_docs > 0 else 0:.1f}%")
            
        else:
            print("\n⚠️  No claims with documents found in MongoDB")
            print("   This could mean:")
            print("   - No claims have been submitted yet")
            print("   - Documents are not being saved to MongoDB")
            print("   - Backend server needs to be restarted")
        
        # Get recent claims
        print(f"\n📅 Recent Claims (Last 24 Hours):")
        print("-" * 70)
        from datetime import datetime, timedelta
        recent_time = datetime.utcnow() - timedelta(hours=24)
        
        recent_cursor = coll.find({'created_at': {'$gte': recent_time}}).sort('created_at', -1)
        recent_claims = await recent_cursor.to_list(length=10)
        
        if recent_claims:
            print(f"✅ Found {len(recent_claims)} claim(s) in last 24 hours")
            for claim in recent_claims[:3]:
                claim_id = claim.get('_id', 'N/A')
                doc_count = len(claim.get('documents', []))
                created = claim.get('created_at', 'N/A')
                print(f"   - Claim {claim_id}: {doc_count} document(s) - {created}")
        else:
            print("⚠️  No recent claims found")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking MongoDB: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'client' in locals():
            client.close()

def main():
    """Run verification"""
    print("\n🔍 Verifying Claim Documents in MongoDB\n")
    
    success = asyncio.run(verify_claim_documents_in_mongodb())
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    
    if success:
        print("\n✅ MongoDB verification complete")
        print("   Check the output above for document structure details")
    else:
        print("\n❌ MongoDB verification failed")
        print("   Check .env file and MongoDB connection")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except ImportError:
        print("❌ motor not installed")
        print("   Install with: pip install motor")
        exit(1)
    
    main()

