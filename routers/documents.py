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

# Folder mapping for document types (also available in document_utils.py)
FOLDER_MAP = {
    "kyc_document": "kyc",
    "id_card": "id_cards",
    "pan_card": "pan_cards",
    "policy_document": "policies",
    "claim_document": "claims",
    "other": "other"
}

def derive_folder_path(userId: int, documentType: str, claimId: Optional[int] = None) -> str:
    """
    Derive the folder path for a document based on user ID, document type, and optional claim ID.
    
    This function implements the folder structure logic. For migration scripts and standalone use,
    see document_utils.py which contains the same function.
    
    Args:
        userId: User ID
        documentType: Type of document
        claimId: Optional claim ID (used for claim_document type)
    
    Returns:
        Folder path string (e.g., "users/123/kyc", "claims/456")
    """
    base_folder = FOLDER_MAP.get(documentType, "other")
    
    # Handle claims documents separately
    if documentType == "claim_document" and claimId:
        return f"claims/{claimId}"
    elif documentType == "claim_document" and not claimId:
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
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Determine folder structure using helper function
        folder = derive_folder_path(user_id, documentType, claim_id)
        logger.info(f"[DOCUMENT_UPLOAD] Derived folder path: '{folder}' from documentType: '{documentType}'")

        # Upload to Azure Blob Storage if configured, otherwise save locally to ./uploads
        if getattr(azure_storage, 'blob_service_client', None):
            try:
                blob_url = azure_storage.upload_file(
                    file_content=file_content,
                    file_name=file.filename,
                    folder=folder
                )
            except Exception:
                logger.exception('Azure upload failed')
                raise
        else:
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

        return {
            "success": True,
            "documentId": document_id,
            "fileName": file.filename,
            "fileUrl": blob_url,
            "fileSize": file_size,
            "documentType": documentType,  # Include documentType in response for frontend use
            "message": "Document uploaded successfully"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        # Log full traceback for debugging
        tb = traceback.format_exc()
        logger.error('Error in /documents/upload: %s\nTraceback:\n%s', str(e), tb)
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}. See server logs for details.")

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

