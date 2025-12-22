# azure_storage.py
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import os
from dotenv import load_dotenv
from typing import Optional
import uuid
from datetime import datetime

load_dotenv()

class AzureStorageService:
    """Service for handling Azure Blob Storage operations"""
    
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "insurance-documents")
        
        if not self.connection_string:
            # Make Azure Storage optional - log warning but don't raise error
            print("WARNING: AZURE_STORAGE_CONNECTION_STRING environment variable is not set. File upload functionality will be disabled.")
            self.blob_service_client = None
            return
        
        # Initialize BlobServiceClient
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            # Ensure container exists
            self._ensure_container_exists()
        except Exception as e:
            print(f"WARNING: Failed to initialize Azure Storage: {e}. File upload functionality will be disabled.")
            self.blob_service_client = None
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        if not self.blob_service_client:
            return
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"Container '{self.container_name}' created successfully")
        except Exception as e:
            print(f"Error ensuring container exists: {e}")
            raise
    
    def upload_file(self, file_content: bytes, file_name: str, folder: Optional[str] = None) -> str:
        """
        Upload a file to Azure Blob Storage with support for nested folder paths.
        
        Azure Blob Storage supports nested folder structures by using '/' in blob names.
        Examples of valid folder paths:
        - 'users/123/kyc' -> creates nested structure users/123/kyc/
        - 'claims/456' -> creates nested structure claims/456/
        - 'users/123/id_cards' -> creates nested structure users/123/id_cards/
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            folder: Optional folder path supporting nested directories
                   (e.g., 'users/123/kyc', 'claims/456', 'users/123/policies')
        
        Returns:
            Blob URL of the uploaded file
        """
        if not self.blob_service_client:
            raise ValueError("Azure Storage is not configured. Please set AZURE_STORAGE_CONNECTION_STRING environment variable.")
        try:
            # Generate unique file name to avoid conflicts
            file_extension = os.path.splitext(file_name)[1]
            unique_file_name = f"{uuid.uuid4()}{file_extension}"
            
            # Construct blob path with nested folder support
            # Azure Blob Storage automatically creates virtual folders when using '/' in blob names
            if folder:
                # Normalize folder path (remove leading/trailing slashes)
                folder = folder.strip('/')
                blob_name = f"{folder}/{unique_file_name}"
            else:
                blob_name = unique_file_name
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Upload file
            blob_client.upload_blob(file_content, overwrite=True)
            
            # Return blob URL
            blob_url = blob_client.url
            return blob_url
        
        except Exception as e:
            print(f"Error uploading file to Azure Storage: {e}")
            raise
    
    def download_file(self, blob_name: str) -> bytes:
        """
        Download a file from Azure Blob Storage
        
        Args:
            blob_name: Name of the blob to download
        
        Returns:
            File content as bytes
        """
        if not self.blob_service_client:
            raise ValueError("Azure Storage is not configured. Please set AZURE_STORAGE_CONNECTION_STRING environment variable.")
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            if not blob_client.exists():
                raise FileNotFoundError(f"Blob '{blob_name}' does not exist")
            
            # Download file
            download_stream = blob_client.download_blob()
            file_content = download_stream.readall()
            
            return file_content
        
        except Exception as e:
            print(f"Error downloading file from Azure Storage: {e}")
            raise
    
    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Azure Blob Storage.
        Supports nested folder paths in blob_name.
        
        Args:
            blob_name: Full blob path including folder structure
                     (e.g., 'users/123/kyc/uuid.pdf', 'claims/456/uuid.pdf')
        
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.blob_service_client:
            raise ValueError("Azure Storage is not configured. Please set AZURE_STORAGE_CONNECTION_STRING environment variable.")
        try:
            # Normalize blob name (remove leading slash if present)
            blob_name = blob_name.lstrip('/')
            
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            if not blob_client.exists():
                return False
            
            # Delete blob
            blob_client.delete_blob()
            return True
        
        except Exception as e:
            print(f"Error deleting file from Azure Storage: {e}")
            return False
    
    def get_file_url(self, blob_name: str) -> str:
        """
        Get the URL of a file in Azure Blob Storage
        
        Args:
            blob_name: Name of the blob
        
        Returns:
            Blob URL
        """
        if not self.blob_service_client:
            raise ValueError("Azure Storage is not configured. Please set AZURE_STORAGE_CONNECTION_STRING environment variable.")
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url
    
    def list_files(self, folder: Optional[str] = None, prefix: Optional[str] = None) -> list:
        """
        List files in Azure Blob Storage with support for nested folder paths.
        
        Args:
            folder: Optional folder path supporting nested directories
                   (e.g., 'users/123/kyc', 'claims/456')
            prefix: Optional prefix to filter files within the folder
        
        Returns:
            List of blob names (full paths including folder structure)
        
        Example:
            list_files(folder='users/123/kyc') -> ['users/123/kyc/uuid1.pdf', 'users/123/kyc/uuid2.pdf']
        """
        if not self.blob_service_client:
            return []
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # Normalize folder path
            if folder:
                folder = folder.strip('/')
            
            # Construct prefix for nested folder structure
            if folder and prefix:
                search_prefix = f"{folder}/{prefix}"
            elif folder:
                search_prefix = f"{folder}/"
            elif prefix:
                search_prefix = prefix
            else:
                search_prefix = None
            
            # List blobs with prefix (supports nested folders)
            blobs = container_client.list_blobs(name_starts_with=search_prefix)
            return [blob.name for blob in blobs]
        
        except Exception as e:
            print(f"Error listing files from Azure Storage: {e}")
            return []

# Initialize Azure Storage Service
azure_storage = AzureStorageService()

