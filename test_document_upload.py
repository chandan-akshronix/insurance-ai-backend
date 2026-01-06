"""
Test script to diagnose document upload issues
This tests the upload endpoint directly to identify problems
"""
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_document_upload():
    """Test document upload endpoint"""
    print("=" * 70)
    print("TASK 1.4: TESTING DOCUMENT UPLOAD FLOW")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    upload_endpoint = f"{base_url}/documents/upload"
    
    print(f"\n📡 Testing upload endpoint: {upload_endpoint}")
    
    # Check if server is running
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend server is running")
        else:
            print(f"⚠️  Backend server returned status {health_response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend server is NOT running!")
        print("   Please start the server: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"⚠️  Could not check server status: {e}")
    
    # Check storage health
    try:
        storage_response = requests.get(f"{base_url}/health/storage", timeout=5)
        if storage_response.status_code == 200:
            storage_data = storage_response.json()
            print(f"\n📦 Storage Status:")
            print(f"   Azure Configured: {storage_data.get('azure_configured', False)}")
            print(f"   Azure Connected: {storage_data.get('azure_connected', False)}")
            print(f"   Storage Type: {storage_data.get('storage_type', 'unknown')}")
            print(f"   Container: {storage_data.get('container_name', 'unknown')}")
            print(f"   Status: {storage_data.get('status', 'unknown')}")
            
            if storage_data.get('azure_connected'):
                print("   ✅ Azure Storage is connected and ready")
            else:
                print("   ⚠️  Azure Storage is not connected - will use local storage")
        else:
            print(f"⚠️  Could not check storage status: {storage_response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not check storage health: {e}")
    
    # Create a test file
    test_file_content = b"This is a test document for upload testing."
    test_file_path = Path("test_upload_file.txt")
    
    try:
        with open(test_file_path, 'wb') as f:
            f.write(test_file_content)
        print(f"\n📄 Created test file: {test_file_path}")
        
        # Test upload
        print(f"\n🔄 Testing document upload...")
        
        files = {
            'file': ('test_upload_file.txt', open(test_file_path, 'rb'), 'text/plain')
        }
        
        data = {
            'userId': '1',
            'documentType': 'claim_document',
            'claimId': '999'  # Test claim ID
        }
        
        print(f"   Sending request with:")
        print(f"   - userId: {data['userId']}")
        print(f"   - documentType: {data['documentType']}")
        print(f"   - claimId: {data['claimId']}")
        
        response = requests.post(upload_endpoint, files=files, data=data, timeout=30)
        
        files['file'][1].close()  # Close the file
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\n✅ Upload successful!")
                print(f"   Response: {result}")
                
                # Check response structure
                print(f"\n📋 Response Structure Check:")
                has_fileUrl = 'fileUrl' in result or 'fileurl' in result
                has_documentId = 'documentId' in result or 'document_id' in result
                has_fileName = 'fileName' in result or 'filename' in result
                
                print(f"   ✅ fileUrl present: {has_fileUrl}")
                if has_fileUrl:
                    file_url = result.get('fileUrl') or result.get('fileurl')
                    print(f"      URL: {file_url}")
                    if 'blob.core.windows.net' in (file_url or ''):
                        print(f"      ✅ Azure Blob Storage URL detected")
                    elif '/uploads/' in (file_url or ''):
                        print(f"      ⚠️  Local storage URL detected")
                
                print(f"   ✅ documentId present: {has_documentId}")
                if has_documentId:
                    doc_id = result.get('documentId') or result.get('document_id')
                    print(f"      ID: {doc_id}")
                
                print(f"   ✅ fileName present: {has_fileName}")
                if has_fileName:
                    file_name = result.get('fileName') or result.get('filename')
                    print(f"      Name: {file_name}")
                
                if has_fileUrl and has_documentId:
                    print(f"\n✅ Response structure is correct - frontend should be able to process this")
                else:
                    print(f"\n⚠️  Response structure may be incomplete")
                    print(f"   Frontend expects: fileUrl, documentId, fileName")
                
                return True
                
            except Exception as e:
                print(f"\n❌ Failed to parse response as JSON: {e}")
                print(f"   Response text: {response.text[:500]}")
                return False
        else:
            print(f"\n❌ Upload failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ Upload timed out (30 seconds)")
        print(f"   This could indicate:")
        print(f"   - Network issues")
        print(f"   - Azure Storage connection problems")
        print(f"   - Large file size")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection error")
        print(f"   Backend server may not be running")
        return False
    except Exception as e:
        print(f"\n❌ Error during upload test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup test file
        if test_file_path.exists():
            test_file_path.unlink()
            print(f"\n🧹 Cleaned up test file")

def test_multiple_uploads():
    """Test multiple document uploads"""
    print("\n" + "=" * 70)
    print("TESTING MULTIPLE DOCUMENT UPLOADS")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    upload_endpoint = f"{base_url}/documents/upload"
    
    test_files = [
        ("test_doc1.txt", b"Test document 1 content"),
        ("test_doc2.txt", b"Test document 2 content"),
        ("test_doc3.txt", b"Test document 3 content"),
    ]
    
    results = []
    
    for file_name, file_content in test_files:
        test_file_path = Path(file_name)
        try:
            with open(test_file_path, 'wb') as f:
                f.write(file_content)
            
            files = {
                'file': (file_name, open(test_file_path, 'rb'), 'text/plain')
            }
            
            data = {
                'userId': '1',
                'documentType': 'claim_document',
                'claimId': '999'
            }
            
            print(f"\n🔄 Uploading {file_name}...")
            response = requests.post(upload_endpoint, files=files, data=data, timeout=30)
            files['file'][1].close()
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    'file': file_name,
                    'success': True,
                    'fileUrl': result.get('fileUrl') or result.get('fileurl'),
                    'documentId': result.get('documentId') or result.get('document_id')
                })
                print(f"   ✅ Success")
            else:
                results.append({
                    'file': file_name,
                    'success': False,
                    'error': response.text[:200]
                })
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            results.append({
                'file': file_name,
                'success': False,
                'error': str(e)
            })
            print(f"   ❌ Error: {e}")
        finally:
            if test_file_path.exists():
                test_file_path.unlink()
    
    print(f"\n📊 Multiple Upload Results:")
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"   ✅ Successful: {len(successful)}/{len(results)}")
    print(f"   ❌ Failed: {len(failed)}/{len(results)}")
    
    if failed:
        print(f"\n   Failed uploads:")
        for r in failed:
            print(f"      - {r['file']}: {r.get('error', 'Unknown error')}")

def main():
    """Run all diagnostic tests"""
    print("\n" + "=" * 70)
    print("DOCUMENT UPLOAD DIAGNOSTIC TEST")
    print("=" * 70)
    print("\nThis script tests the document upload endpoint to identify issues\n")
    
    # Test single upload
    single_success = test_document_upload()
    
    if single_success:
        # Test multiple uploads
        test_multiple_uploads()
    
    print("\n" + "=" * 70)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 70)
    
    if single_success:
        print("\n✅ Upload endpoint is working correctly")
        print("   If frontend still shows errors, check:")
        print("   - Browser console for detailed logs")
        print("   - Network tab for API responses")
        print("   - Category mapping in frontend code")
    else:
        print("\n❌ Upload endpoint has issues")
        print("   Check:")
        print("   - Backend server is running")
        print("   - Azure Storage is configured")
        print("   - Backend logs for errors")
    
    print("=" * 70 + "\n")

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("❌ requests library not installed")
        print("   Install with: pip install requests")
        exit(1)
    
    main()

