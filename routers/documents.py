from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from datetime import date
import os
import uuid
import logging
import traceback
import schemas, models, crud
from database import get_db
from azure_storage import azure_storage
from typing import Optional

router = APIRouter(prefix="/documents", tags=["Documents"])

logger = logging.getLogger(__name__)

# Allowed document types for validation
ALLOWED_DOCUMENT_TYPES = {
    "kyc_document",
    "id_card",
    "pan_card",
    "policy_document",
    "claim_document",
    "other"
}

# Allowed file extensions
ALLOWED_FILE_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".doc", ".docx", ".xls", ".xlsx", ".txt"
}

# Maximum file size: 10 MB (10 * 1024 * 1024 bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Folder mapping for document types (also available in document_utils.py)
FOLDER_MAP = {
    "kyc_document": "kyc",
    "id_card": "id_cards",
    "pan_card": "pan_cards",
    "policy_document": "policies",
    "claim_document": "claims",
    "other": "other"
}

def normalize_category_for_folder(category: str) -> str:
    """
    Normalize category name for use in folder paths.
    
    Converts category names to folder-safe format:
    - Lowercase
    - Replace spaces and underscores with hyphens
    - Remove special characters except hyphens and alphanumeric
    
    Args:
        category: Category name (e.g., "Death Certificate", "FIR Copy (if accidental)")
    
    Returns:
        Normalized category name (e.g., "death-certificate", "fir-copy-if-accidental")
    
    Examples:
        >>> normalize_category_for_folder("Death Certificate")
        "death-certificate"
        >>> normalize_category_for_folder("FIR Copy (if accidental)")
        "fir-copy-if-accidental"
        >>> normalize_category_for_folder("Claim Form")
        "claim-form"
    """
    import re
    # Convert to lowercase
    normalized = category.lower()
    # Replace spaces and underscores with hyphens
    normalized = normalized.replace(' ', '-').replace('_', '-')
    # Remove any special characters except hyphens and alphanumeric
    normalized = re.sub(r'[^a-z0-9\-]', '', normalized)
    # Remove multiple consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized

def derive_folder_path(userId: int, documentType: str, claimId: Optional[int] = None, category: Optional[str] = None) -> str:
    """
    Derive the folder path for a document based on user ID, document type, optional claim ID, and category.
    
    This function implements the folder structure logic. For migration scripts and standalone use,
    see document_utils.py which contains the same function.
    
    Args:
        userId: User ID
        documentType: Type of document
        claimId: Optional claim ID (used for claim_document type)
        category: Optional category/name for claim documents (e.g., "death-certificate", "claim-form")
    
    Returns:
        Folder path string (e.g., "users/123/kyc", "claims/456/death-certificate", "claims/pending/123/claim-form")
    """
    base_folder = FOLDER_MAP.get(documentType, "other")
    
    # Handle claims documents separately with category subfolders
    if documentType == "claim_document":
        if claimId:
            # For claim documents with claimId: claims/{claimId}/{category}/
            if category:
                # Normalize category for folder name using helper function
                normalized_category = normalize_category_for_folder(category)
                logger.debug(f"[FOLDER_PATH] Normalized category '{category}' -> '{normalized_category}'")
                return f"claims/{claimId}/{normalized_category}"
            else:
                # Fallback to old structure if no category provided (backward compatibility)
                return f"claims/{claimId}"
        else:
            # For pending claims: claims/pending/{userId}/{category}/
            if category:
                normalized_category = normalize_category_for_folder(category)
                logger.debug(f"[FOLDER_PATH] Normalized category '{category}' -> '{normalized_category}'")
                return f"claims/pending/{userId}/{normalized_category}"
            else:
                # Fallback to old structure if no category provided (backward compatibility)
                return f"claims/pending/{userId}"
    else:
        # User documents organized by userId and document type
        return f"users/{userId}/{base_folder}"

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    userId: str = Form(...),
    documentType: str = Form(...),
    policyId: Optional[str] = Form(None),
    claimId: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document to Azure Blob Storage and save metadata to database.
    Documents are organized in user-specific folders: users/{userId}/{documentType}/
    Claims documents are organized separately: claims/{claimId}/
    """
    try:
        # Convert userId to int
        try:
            user_id = int(userId) if userId else None
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="userId must be a valid integer")
        
        if user_id is None:
            raise HTTPException(status_code=400, detail="userId is required")
        
        # Log received documentType for debugging
        logger.info(f"[DOCUMENT_UPLOAD] Received documentType: '{documentType}' for userId: {userId}, fileName: {file.filename}")
        
        # Validate documentType
        if not documentType or not documentType.strip():
            logger.error(f"[DOCUMENT_UPLOAD] Invalid documentType: empty or None for userId: {userId}, fileName: {file.filename}")
            raise HTTPException(status_code=400, detail="documentType is required and cannot be empty")
        
        documentType = documentType.strip()  # Normalize whitespace
        
        if documentType not in ALLOWED_DOCUMENT_TYPES:
            allowed_types_str = ", ".join(sorted(ALLOWED_DOCUMENT_TYPES))
            logger.error(f"[DOCUMENT_UPLOAD] Invalid documentType: '{documentType}' for userId: {userId}, fileName: {file.filename}. Allowed types: {allowed_types_str}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid documentType: '{documentType}'. Allowed types are: {allowed_types_str}"
            )
        
        logger.info(f"[DOCUMENT_UPLOAD] DocumentType validated: '{documentType}' for userId: {userId}")
        
        # Convert optional fields to integers if provided
        try:
            policy_id = int(policyId) if policyId and str(policyId).strip() else None
        except (ValueError, TypeError):
            policy_id = None
        
        try:
            claim_id = int(claimId) if claimId and str(claimId).strip() else None
        except (ValueError, TypeError):
            claim_id = None
        
        # Validate file name
        if not file.filename or not file.filename.strip():
            logger.error(f"[DOCUMENT_UPLOAD] Empty filename for userId: {userId}")
            raise HTTPException(status_code=400, detail="File name is required")
        
        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_FILE_EXTENSIONS:
            allowed_ext_str = ", ".join(sorted(ALLOWED_FILE_EXTENSIONS))
            logger.error(f"[DOCUMENT_UPLOAD] Invalid file extension: '{file_ext}' for fileName: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed extensions are: {allowed_ext_str}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size == 0:
            logger.error(f"[DOCUMENT_UPLOAD] Empty file for userId: {userId}, fileName: {file.filename}")
            raise HTTPException(status_code=400, detail="File is empty. Please upload a valid file.")
        
        if file_size > MAX_FILE_SIZE:
            max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            logger.error(f"[DOCUMENT_UPLOAD] File too large: {file_size_mb:.2f} MB (max: {max_size_mb} MB) for fileName: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB). Please upload a smaller file."
            )
        
        logger.info(f"[DOCUMENT_UPLOAD] File validation passed - size: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB), extension: {file_ext}")

        # Determine folder structure using helper function
        # Normalize and validate category if provided (for claim documents)
        normalized_category = None
        if category and category.strip():
            category_input = category.strip()
            logger.info(f"[DOCUMENT_UPLOAD] Category provided: '{category_input}' for documentType: '{documentType}'")
            
            # Normalize category to folder-safe format using helper function
            normalized_category = normalize_category_for_folder(category_input)
            logger.info(f"[DOCUMENT_UPLOAD] Normalized category: '{category_input}' -> '{normalized_category}'")
            
            # Validate category if claim type can be determined
            # Note: We don't have claim type here, so we'll validate at MongoDB update stage
            # But we can still normalize it for folder structure
        
        folder = derive_folder_path(user_id, documentType, claim_id, normalized_category)
        logger.info(f"[DOCUMENT_UPLOAD] Derived folder path: '{folder}'")
        logger.info(f"[DOCUMENT_UPLOAD]   - documentType: '{documentType}'")
        logger.info(f"[DOCUMENT_UPLOAD]   - category: '{normalized_category}'")
        logger.info(f"[DOCUMENT_UPLOAD]   - claimId: '{claim_id}'")
        
        # Log folder structure breakdown for category-based folders
        if documentType == "claim_document" and normalized_category:
            folder_parts = folder.split('/')
            if len(folder_parts) >= 2:
                logger.info(f"[DOCUMENT_UPLOAD] 📁 Category-based folder structure:")
                logger.info(f"[DOCUMENT_UPLOAD]   Base: {folder_parts[0]}")
                if len(folder_parts) >= 2:
                    logger.info(f"[DOCUMENT_UPLOAD]   Claim/Pending: {folder_parts[1]}")
                if len(folder_parts) >= 3:
                    logger.info(f"[DOCUMENT_UPLOAD]   Category: {folder_parts[2]} (normalized from: '{normalized_category}')")
                if len(folder_parts) >= 4:
                    logger.info(f"[DOCUMENT_UPLOAD]   Sub-category: {folder_parts[3]}")

        # Upload to Azure Blob Storage if configured, otherwise save locally to ./uploads
        if getattr(azure_storage, 'blob_service_client', None):
            try:
                logger.info(f"[DOCUMENT_UPLOAD] Uploading to Azure Blob Storage - folder: '{folder}', fileName: '{file.filename}', size: {file_size:,} bytes")
                blob_url = azure_storage.upload_file(
                    file_content=file_content,
                    file_name=file.filename,
                    folder=folder
                )
                
                # Verify Azure URL format
                if 'blob.core.windows.net' in blob_url:
                    logger.info(f"[DOCUMENT_UPLOAD] ✅ Successfully uploaded to Azure Blob Storage")
                    logger.info(f"[DOCUMENT_UPLOAD]   URL: {blob_url[:100]}...")
                else:
                    logger.warning(f"[DOCUMENT_UPLOAD] ⚠️  Uploaded but URL doesn't match Azure format: {blob_url[:100]}...")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[DOCUMENT_UPLOAD] ❌ Azure upload failed: {error_msg}")
                logger.exception('Full Azure upload error traceback')
                
                # Provide more specific error messages for Azure errors
                if 'Azure' in error_msg or 'blob' in error_msg.lower() or 'storage' in error_msg.lower() or 'connection' in error_msg.lower():
                    raise HTTPException(
                        status_code=500,
                        detail=f"Azure Storage error: Unable to upload to cloud storage. Please try again or contact support if the issue persists."
                    )
                elif 'timeout' in error_msg.lower():
                    raise HTTPException(
                        status_code=504,
                        detail="Upload timeout: The upload took too long. Please try again with a smaller file or check your connection."
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Upload failed: {error_msg}. Please try again."
                    )
        else:
            logger.warning(f"[DOCUMENT_UPLOAD] Azure Storage not configured, saving to local storage - folder: '{folder}'")
            # fallback local save with nested folder structure
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            # use unique filename
            ext = os.path.splitext(file.filename)[1]
            unique_name = f"{uuid.uuid4()}{ext}"
            # Create nested folder structure (creates all parent directories if needed)
            dest_folder = os.path.join(uploads_dir, folder)
            os.makedirs(dest_folder, exist_ok=True, parents=True)
            dest_path = os.path.join(dest_folder, unique_name)
            with open(dest_path, 'wb') as fh:
                fh.write(file_content)
            # Use request.base_url to construct accessible URL with nested path
            # Normalize folder path to use forward slashes for URLs (works on all OS)
            folder_url_path = folder.replace('\\', '/')
            # Ensure base_url ends with / and URL path doesn't start with /
            base_url = str(request.base_url).rstrip('/')
            blob_url = f"{base_url}/uploads/{folder_url_path}/{unique_name}"
        
        # Create document record in database
        logger.info(f"[DOCUMENT_UPLOAD] Preparing to save to database - documentType: '{documentType}', userId: {user_id}, fileName: {file.filename}")
        document_data = schemas.DocumentCreate(
            userId=user_id,
            policyId=policy_id,
            documentType=documentType,
            documentUrl=blob_url,
            uploadDate=date.today(),
            fileSize=file_size
        )
        
        document_id = crud.create_entry(db, models.Documents, document_data, return_id=True)
        
        # Verify what was actually saved to database
        saved_document = crud.get_by_id(db, models.Documents, "id", document_id)
        if saved_document:
            logger.info(f"[DOCUMENT_UPLOAD] Document saved successfully. ID: {document_id}, Saved documentType: '{saved_document.documentType}', URL folder: '{saved_document.documentUrl}'")
        else:
            logger.warning(f"[DOCUMENT_UPLOAD] Document saved but could not retrieve for verification. ID: {document_id}")

        # Ensure consistent response format (camelCase for frontend compatibility)
        response = {
            "success": True,
            "documentId": document_id,
            "fileName": file.filename,
            "fileUrl": blob_url,  # Primary field name (camelCase)
            "fileSize": file_size,
            "documentType": documentType,  # Include documentType in response for frontend use
            "message": "Document uploaded successfully"
        }
        
        # Log response for debugging
        logger.info(f"[DOCUMENT_UPLOAD] ✅ Upload successful - Returning response:")
        logger.info(f"[DOCUMENT_UPLOAD]   documentId: {document_id}")
        logger.info(f"[DOCUMENT_UPLOAD]   fileName: {file.filename}")
        logger.info(f"[DOCUMENT_UPLOAD]   fileUrl: {blob_url[:100]}...")
        logger.info(f"[DOCUMENT_UPLOAD]   fileSize: {file_size:,} bytes")
        logger.info(f"[DOCUMENT_UPLOAD]   documentType: {documentType}")
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Log full traceback for debugging
        tb = traceback.format_exc()
        logger.error('[DOCUMENT_UPLOAD] ❌ Error in /documents/upload: %s', str(e))
        logger.error('[DOCUMENT_UPLOAD] Traceback:\n%s', tb)
        
        # Return user-friendly error message
        error_detail = str(e)
        if "Azure" in error_detail or "blob" in error_detail.lower():
            error_detail = "Failed to upload document to storage. Please try again."
        elif "database" in error_detail.lower() or "SQL" in error_detail:
            error_detail = "Failed to save document record. Please try again."
        else:
            error_detail = f"Error uploading document: {error_detail}"
        
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/")
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a document record (when file is already uploaded)
    """
    document_id = crud.create_entry(db, models.Documents, document, return_id=True)
    return {
        "success": True,
        "documentId": document_id,
        "message": "Document created successfully"
    }

@router.get("/", response_model=list[schemas.Document])
def read_documents(db: Session = Depends(get_db)):
    documents = crud.get_all(db, models.Documents)
    return [{"documentId": d.id,
             "userId": d.userId,
             "policyId": d.policyId,
             "documentType": d.documentType,
             "documentUrl": d.documentUrl,
             "uploadDate": d.uploadDate,
             "fileSize": d.fileSize} for d in documents]

@router.get("/user/{user_id}", response_model=list[schemas.Document])
def get_documents_by_user(user_id: int, db: Session = Depends(get_db)):
    documents = crud.get_documents_by_user(db, user_id)
    return [{"documentId": d.id,
             "userId": d.userId,
             "policyId": d.policyId,
             "documentType": d.documentType,
             "documentUrl": d.documentUrl,
             "uploadDate": d.uploadDate,
             "fileSize": d.fileSize} for d in documents]

@router.get("/policy/{policy_id}", response_model=list[schemas.Document])
def get_documents_by_policy(policy_id: int, db: Session = Depends(get_db)):
    documents = crud.get_documents_by_policy(db, policy_id)
    return [{"documentId": d.id,
             "userId": d.userId,
             "policyId": d.policyId,
             "documentType": d.documentType,
             "documentUrl": d.documentUrl,
             "uploadDate": d.uploadDate,
             "fileSize": d.fileSize} for d in documents]

@router.get("/{document_id}", response_model=schemas.Document)
def read_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_by_id(db, models.Documents, "id", document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "documentId": document.id,
        "userId": document.userId,
        "policyId": document.policyId,
        "documentType": document.documentType,
        "documentUrl": document.documentUrl,
        "uploadDate": document.uploadDate,
        "fileSize": document.fileSize
    }

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document from database and Azure Blob Storage
    """
    document = crud.get_by_id(db, models.Documents, "id", document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Extract blob path from URL for nested folder structure
        blob_url = document.documentUrl
        
        # Handle Azure Blob Storage URLs
        if 'blob.core.windows.net' in blob_url:
            # Extract the full blob path from Azure URL
            # Format: https://accountname.blob.core.windows.net/container/path/to/file
            container_name = getattr(azure_storage, 'container_name', 'insurance-documents')
            # Split by container name to get the blob path
            if f'/{container_name}/' in blob_url:
                blob_name = blob_url.split(f'/{container_name}/')[-1]
            else:
                # Fallback: extract everything after the last known separator
                blob_name = '/'.join(blob_url.split('/')[4:])  # Skip https://, account, blob.core.windows.net, container
        else:
            # Handle local storage URLs
            # Format: http://localhost:8000/uploads/path/to/file
            if '/uploads/' in blob_url:
                blob_name = blob_url.split('/uploads/')[-1]
            else:
                blob_name = blob_url.split('/')[-1]
        
        # Delete from Azure Blob Storage (if configured)
        if getattr(azure_storage, 'blob_service_client', None):
            azure_storage.delete_file(blob_name)
        else:
            # Delete from local storage
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            file_path = os.path.join(uploads_dir, blob_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Delete from database
        success = crud.delete_by_id(db, models.Documents, "id", document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

