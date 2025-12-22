from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import date
import schemas, models, crud
from database import get_db
from azure_storage import azure_storage
from typing import Optional

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    userId: int = Form(...),
    policyId: int = Form(...),
    documentType: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document to Azure Blob Storage and save metadata to database
    """
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Determine folder based on document type
        folder_map = {
            "policy_document": "policies",
            "claim_document": "claims",
            "kyc_document": "kyc",
            "other": "documents"
        }
        folder = folder_map.get(documentType, "documents")
        
        # Upload to Azure Blob Storage
        blob_url = azure_storage.upload_file(
            file_content=file_content,
            file_name=file.filename,
            folder=folder
        )
        
        # Create document record in database
        document_data = schemas.DocumentCreate(
            userId=userId,
            policyId=policyId,
            documentType=documentType,
            documentUrl=blob_url,
            uploadDate=date.today(),
            fileSize=file_size
        )
        
        document_id = crud.create_entry(db, models.Documents, document_data, return_id=True)
        
        return {
            "success": True,
            "documentId": document_id.id,
            "fileName": file.filename,
            "fileUrl": blob_url,
            "fileSize": file_size,
            "message": "Document uploaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.post("/")
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a document record (when file is already uploaded)
    """
    document_id = crud.create_entry(db, models.Documents, document, return_id=True)
    return {
        "success": True,
        "documentId": document_id.id,
        "fileName": document_id.documentType,
        "fileUrl": document_id.documentUrl,
        "message": "Document created successfully"
    }

@router.get("/", response_model=list[schemas.Document])
def read_documents(db: Session = Depends(get_db)):
    return crud.get_all(db, models.Documents)

@router.get("/user/{user_id}", response_model=list[schemas.Document])
def get_documents_by_user(user_id: int, db: Session = Depends(get_db)):
    documents = crud.get_documents_by_user(db, user_id)
    return documents

@router.get("/policy/{policy_id}", response_model=list[schemas.Document])
def get_documents_by_policy(policy_id: int, db: Session = Depends(get_db)):
    documents = crud.get_documents_by_policy(db, policy_id)
    return documents

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
        # Extract blob name from URL
        # Azure blob URL format: https://accountname.blob.core.windows.net/container/blobname
        blob_url = document.documentUrl
        blob_name = blob_url.split('/')[-1]  # Get the last part of URL
        
        # Delete from Azure Blob Storage
        azure_storage.delete_file(blob_name)
        
        # Delete from database
        success = crud.delete_by_id(db, models.Documents, "id", document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

