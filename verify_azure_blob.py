from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os

load_dotenv()

CONN_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'insurance-documents')
TEST_BLOB_NAME = 'test_blob.txt'
TEST_BLOB_CONTENT = b'This is a test blob from connection test.'

print('Testing Azure Blob Storage connection...')

if not CONN_STR:
    print('❌ AZURE_STORAGE_CONNECTION_STRING not found in environment.')
    print('Please set AZURE_STORAGE_CONNECTION_STRING in .env or environment variables.')
    raise SystemExit(1)

try:
    client = BlobServiceClient.from_connection_string(CONN_STR)
    print('✅ Created BlobServiceClient')

    # Create container if not exists
    container_client = client.get_container_client(CONTAINER)
    try:
        container_client.create_container()
        print(f"✅ Created container '{CONTAINER}'")
    except Exception as e:
        # container may already exist
        print(f"ℹ️ Container '{CONTAINER}' may already exist or cannot be created: {e}")

    # Upload blob
    blob_client = container_client.get_blob_client(TEST_BLOB_NAME)
    blob_client.upload_blob(TEST_BLOB_CONTENT, overwrite=True)
    print(f"✅ Uploaded test blob '{TEST_BLOB_NAME}'")

    # List blobs in container
    print('\nListing blobs in container:')
    blobs = list(container_client.list_blobs())
    for b in blobs:
        print(' -', b.name)

    # Download blob and verify content
    downloader = blob_client.download_blob()
    data = downloader.readall()
    print('\n✅ Downloaded blob content:')
    print(data.decode('utf-8'))

    # Delete blob (cleanup)
    blob_client.delete_blob()
    print(f"✅ Deleted test blob '{TEST_BLOB_NAME}' (cleanup)")

    print('\nAzure Blob Storage test completed successfully.')

except Exception as e:
    print('\n❌ Azure Blob Storage test failed:')
    print(str(e))
    raise
