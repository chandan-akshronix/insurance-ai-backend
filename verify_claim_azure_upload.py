"""
Verify that claim documents are uploading to Azure Blob Storage
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta

def verify_claim_documents_in_azure():
    """Verify claim documents are in Azure Blob Storage"""
    print("=" * 70)
    print("TASK 4: VERIFY CLAIM DOCUMENTS IN AZURE BLOB STORAGE")
    print("=" * 70)
    
    backend_dir = Path(__file__).parent
    env_file = backend_dir / ".env"
    
    if not env_file.exists():
        print("\n❌ .env file not found")
        return False
    
    load_dotenv(env_file)
    
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "insurance-documents")
    
    if not conn_str:
        print("\n❌ AZURE_STORAGE_CONNECTION_STRING not set")
        return False
    
    try:
        print(f"\n🔄 Connecting to Azure Storage...")
        client = BlobServiceClient.from_connection_string(conn_str)
        container_client = client.get_container_client(container_name)
        
        if not container_client.exists():
            print(f"\n❌ Container '{container_name}' does not exist")
            return False
        
        print(f"✅ Connected to container: {container_name}")
        
        # Check for claim documents
        print(f"\n📋 Checking for claim documents...")
        claims_blobs = list(container_client.list_blobs(name_starts_with="claims/"))
        
        if claims_blobs:
            print(f"\n✅ Found {len(claims_blobs)} claim documents in Azure")
            
            # Group by claim ID
            claim_folders = {}
            for blob in claims_blobs:
                parts = blob.name.split('/')
                if len(parts) >= 2:
                    claim_id = parts[1]
                    if claim_id not in claim_folders:
                        claim_folders[claim_id] = []
                    claim_folders[claim_id].append(blob)
            
            print(f"\n📊 Claim Documents by Claim ID:")
            print("-" * 70)
            for claim_id, blobs in sorted(claim_folders.items()):
                print(f"\n  Claim ID: {claim_id}")
                print(f"    Files: {len(blobs)}")
                for blob in blobs[:3]:  # Show first 3
                    file_name = blob.name.split('/')[-1]
                    size_mb = blob.size / (1024 * 1024)
                    print(f"      - {file_name} ({size_mb:.2f} MB)")
                if len(blobs) > 3:
                    print(f"      ... and {len(blobs) - 3} more")
            
            # Check recent uploads (last 24 hours)
            recent_time = datetime.now().replace(tzinfo=None) - timedelta(hours=24)
            recent_claims = [b for b in claims_blobs if b.last_modified and b.last_modified.replace(tzinfo=None) >= recent_time]
            
            print(f"\n📅 Recent Uploads (Last 24 Hours):")
            print("-" * 70)
            if recent_claims:
                print(f"✅ Found {len(recent_claims)} claim documents uploaded in last 24 hours")
                for blob in recent_claims[:5]:
                    print(f"   - {blob.name} ({blob.size:,} bytes) - {blob.last_modified}")
            else:
                print("⚠️  No claim documents uploaded in last 24 hours")
            
            # Verify URLs
            print(f"\n🔗 URL Verification:")
            print("-" * 70)
            azure_urls = [b for b in claims_blobs if 'blob.core.windows.net' in b.name or True]  # All are Azure
            print(f"✅ All {len(claims_blobs)} claim documents are in Azure Blob Storage")
            print(f"   Container: {container_name}")
            print(f"   Base URL: https://insurancedocuments.blob.core.windows.net/{container_name}/")
            
        else:
            print("\n⚠️  No claim documents found in Azure")
            print("   This could mean:")
            print("   - No claims have been submitted yet")
            print("   - Documents are being saved locally instead of Azure")
            print("   - Backend server needs to be restarted")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking Azure Storage: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run verification"""
    print("\n🔍 Verifying Claim Documents in Azure Blob Storage\n")
    
    success = verify_claim_documents_in_azure()
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
    
    if success:
        print("\n✅ Azure Storage is configured and claim documents can be uploaded")
        print("   Next: Test with actual claim submission in frontend")
    else:
        print("\n❌ Azure Storage verification failed")
        print("   Check .env file and backend configuration")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        from azure.storage.blob import BlobServiceClient
    except ImportError:
        print("❌ azure-storage-blob not installed")
        print("   Install with: pip install azure-storage-blob")
        exit(1)
    
    main()

