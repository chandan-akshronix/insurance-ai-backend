from fastapi import APIRouter, Request, HTTPException
from fastapi import status
from bson import ObjectId
from datetime import datetime
from typing import List
from database import SessionLocal
import crud, models
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/claims", tags=["Claims"])


def _oid_str(doc: dict):
    """Helper to normalize MongoDB document: keep _id as string if it already is,
    or convert ObjectId to string. This ensures JSON output shows plain string id."""
    if not doc:
        return doc
    doc = dict(doc)
    if '_id' in doc:
        # If _id is already a string, keep it; if ObjectId, convert to string
        doc['_id'] = str(doc['_id']) if doc['_id'] else None
    return doc


# ============================================================================
# MongoDB-backed Claim Applications Endpoints (flexible JSON storage)
# ============================================================================

@router.post('/application', status_code=status.HTTP_201_CREATED)
async def create_claim_application(request: Request, payload: dict):
    """
    Accept a flexible JSON payload for claim applications.
    Using a plain `dict` here avoids FastAPI/Pydantic 422 validation when the
    frontend sends camelCase or slightly different shapes. We still set
    timestamps and persist whatever JSON the client provided.
    Stores in MongoDB collection 'claims'.
    """
    db = request.app.mongodb
    coll = db.get_collection('claims')  # Using 'claims' collection as requested
    # ensure we have a mutable dict
    doc = dict(payload or {})

    # Optionally create a SQL Claim if the client provided a `claim` object
    # or `claim` key contains a dict with claim fields. After creating
    # the SQL record we will store its id in the Mongo document under `claim`.
    try:
        claim_obj = doc.get('claim')
        if isinstance(claim_obj, dict):
            sql_db = SessionLocal()
            try:
                claim_payload = {
                    "userId": doc.get('user_id') or doc.get('userId'),
                    "policyId": doc.get('policy_id') or doc.get('policyId'),
                    "claimType": doc.get('claim_type') or doc.get('claimType'),
                    "amount": claim_obj.get('amount', 0.0),
                    "status": claim_obj.get('status', 'Submitted'),
                }
                claim_id = crud.create_entry(sql_db, models.Claim, claim_payload, return_id=True)
                doc['claim'] = claim_id
            finally:
                sql_db.close()
    except Exception:
        import logging
        logging.exception('Failed to create SQL claim from claims-application payload')

    now = datetime.utcnow()
    # only set timestamps if not provided
    doc.setdefault('created_at', now)
    doc['updated_at'] = now
    # Generate a string id upfront so we can store it as _id directly (avoid ObjectId wrapper in JSON)
    doc_id = str(ObjectId())
    doc['_id'] = doc_id
    await coll.insert_one(doc)

    # Create ApplicationProcess entry for tracking
    try:
        sql_db = SessionLocal()
        try:
            # Create the tracking entry for the Admin Panel
            process_data = {
                "applicationId": doc_id,
                "status": "Submitted",  # Initial status
                "currentStep": "ingest",
                "startTime": datetime.utcnow().date(),
                "lastUpdated": datetime.utcnow().date(),
                "customerId": doc.get('user_id') or doc.get('userId'),
                "agentData": {},
                "stepHistory": []
            }
            crud.create_entry(sql_db, models.ApplicationProcess, process_data)
        except Exception as e:
            import logging
            logging.error(f"Failed to create ApplicationProcess entry for claim: {e}")
        finally:
            sql_db.close()
    except Exception as e:
        import logging
        logging.error(f"ApplicationProcess tracking block failed for claim: {e}")

    return {'id': doc_id}


@router.get('/application/user/{user_id}', response_model=List[dict])
async def get_claim_applications_for_user(request: Request, user_id: str):
    """Get all claim applications for a user from MongoDB"""
    db = request.app.mongodb
    coll = db.get_collection('claims')
    # Handle both user_id and userId fields
    cursor = coll.find({
        '$or': [
            {'user_id': user_id},
            {'userId': user_id}
        ]
    }).sort('created_at', -1)
    results = [_oid_str(d) async for d in cursor]
    return results


@router.get('/application/{app_id}')
async def get_claim_application(request: Request, app_id: str):
    """Get a specific claim application by ID from MongoDB"""
    db = request.app.mongodb
    coll = db.get_collection('claims')
    # Query using string _id directly (no ObjectId conversion)
    doc = await coll.find_one({'_id': app_id})
    if not doc:
        raise HTTPException(status_code=404, detail='Claim application not found')
    
    # Log document structure for verification
    if 'documents' in doc:
        documents = doc.get('documents', [])
        logger.info(f"[CLAIM_GET] Retrieved claim application {app_id} with {len(documents)} document(s)")
        for idx, doc_item in enumerate(documents):
            logger.info(f"[CLAIM_GET] Document {idx + 1}:")
            logger.info(f"  - filename: {doc_item.get('filename', 'N/A')}")
            logger.info(f"  - url: {doc_item.get('url', 'N/A')[:100] if doc_item.get('url') else 'N/A'}...")
            logger.info(f"  - documentId: {doc_item.get('documentId', 'N/A')}")
            logger.info(f"  - docType: {doc_item.get('docType', 'N/A')}")
            logger.info(f"  - category: {doc_item.get('category', 'N/A')}")
    else:
        logger.info(f"[CLAIM_GET] Retrieved claim application {app_id} with no documents")
    
    return _oid_str(doc)


@router.patch('/application/{app_id}')
async def update_claim_application(request: Request, app_id: str, payload: dict):
    """Update a claim application in MongoDB"""
    import logging
    logger = logging.getLogger(__name__)
    
    db = request.app.mongodb
    coll = db.get_collection('claims')
    
    # Log the update operation
    logger.info(f"[CLAIM_UPDATE] Updating claim application: {app_id}")
    logger.info(f"[CLAIM_UPDATE] Payload keys: {list(payload.keys())}")
    
    # If documents are being updated, verify and log their structure
    if 'documents' in payload:
        documents = payload.get('documents', [])
        logger.info(f"[CLAIM_UPDATE] Updating with {len(documents)} document(s)")
        
        # Get claim type for category validation
        claim_type = None
        try:
            existing_doc = await coll.find_one({'_id': app_id})
            if existing_doc:
                claim_type = existing_doc.get('claim_type') or existing_doc.get('claimType')
        except Exception as e:
            logger.debug(f"[CLAIM_UPDATE] Could not get claim type: {e}")
        
        # Import category validation functions
        try:
            from category_mapping import is_valid_category, normalize_category_id, get_all_categories_for_claim_type
        except ImportError:
            logger.warning("[CLAIM_UPDATE] Category validation module not available, skipping validation")
            is_valid_category = lambda ct, cat: True
            normalize_category_id = lambda cat: cat.lower().replace(' ', '-')
            get_all_categories_for_claim_type = lambda ct: []
        
        for idx, doc in enumerate(documents):
            logger.info(f"[CLAIM_UPDATE] Document {idx + 1}:")
            logger.info(f"  - filename: {doc.get('filename', 'N/A')}")
            logger.info(f"  - url: {doc.get('url', 'N/A')[:100] if doc.get('url') else 'N/A'}...")
            logger.info(f"  - documentId: {doc.get('documentId', 'N/A')}")
            logger.info(f"  - docType: {doc.get('docType', 'N/A')}")
            logger.info(f"  - category: {doc.get('category', 'N/A')}")
            
            # Verify URL is Azure Blob Storage URL
            url = doc.get('url', '')
            if url and 'blob.core.windows.net' in url:
                logger.info(f"  - ✅ Azure Blob Storage URL verified")
            elif url:
                logger.warning(f"  - ⚠️  URL is not Azure format: {url[:100]}")
            else:
                logger.error(f"  - ❌ Missing URL in document")
            
            # Validate category if claim type is known
            category = doc.get('category', '')
            if category and claim_type:
                normalized_cat = normalize_category_id(category)
                if is_valid_category(claim_type, normalized_cat):
                    logger.info(f"  - ✅ Category '{category}' (normalized: '{normalized_cat}') is valid for claim type '{claim_type}'")
                else:
                    valid_cats = get_all_categories_for_claim_type(claim_type)
                    logger.warning(f"  - ⚠️  Category '{category}' (normalized: '{normalized_cat}') may not be valid for claim type '{claim_type}'")
                    logger.warning(f"  - Valid categories for '{claim_type}': {', '.join(valid_cats[:5])}...")
        
        # Verify all required fields are present
        required_fields = ['filename', 'url', 'docType', 'category']
        for idx, doc in enumerate(documents):
            missing_fields = [field for field in required_fields if not doc.get(field)]
            if missing_fields:
                logger.warning(f"[CLAIM_UPDATE] Document {idx + 1} missing fields: {missing_fields}")
            
            # Verify category matches folder structure in URL
            category = doc.get('category', '')
            url = doc.get('url', '')
            if category and url:
                # Extract folder path from URL to verify category matches
                if 'blob.core.windows.net' in url:
                    # Azure URL format: https://account.blob.core.windows.net/container/folder/file
                    try:
                        url_parts = url.split('blob.core.windows.net/')
                        if len(url_parts) > 1:
                            path_parts = url_parts[1].split('/')
                            if len(path_parts) >= 3:
                                # Check if category is in folder path
                                folder_path = '/'.join(path_parts[1:-1])  # Skip container and filename
                                normalized_category = normalize_category_id(category)
                                
                                if normalized_category in folder_path:
                                    logger.info(f"[CLAIM_UPDATE] ✅ Document {idx + 1} category '{category}' matches folder structure")
                                else:
                                    logger.warning(f"[CLAIM_UPDATE] ⚠️  Document {idx + 1} category '{category}' may not match folder structure: {folder_path}")
                    except Exception as e:
                        logger.debug(f"[CLAIM_UPDATE] Could not verify category match: {e}")
    
    # Query using string _id directly (no ObjectId conversion)
    payload['updated_at'] = datetime.utcnow()
    res = await coll.update_one({'_id': app_id}, {'$set': payload})
    
    if res.matched_count == 0:
        logger.error(f"[CLAIM_UPDATE] Claim application not found: {app_id}")
        raise HTTPException(status_code=404, detail='Claim application not found')
    
    logger.info(f"[CLAIM_UPDATE] ✅ Successfully updated claim application: {app_id}")
    logger.info(f"[CLAIM_UPDATE] Modified count: {res.modified_count}")
    
    # Verify the update by retrieving the document
    updated_doc = await coll.find_one({'_id': app_id})
    if updated_doc and 'documents' in updated_doc:
        saved_docs = updated_doc.get('documents', [])
        logger.info(f"[CLAIM_UPDATE] Verified: {len(saved_docs)} document(s) saved in MongoDB")
        
        # Check backward compatibility - count documents with/without category folders
        try:
            from document_utils import has_category_folder
            docs_with_category_folder = 0
            docs_without_category_folder = 0
            
            for idx, doc in enumerate(saved_docs):
                url = doc.get('url', '')
                category = doc.get('category', '')
                
                if url:
                    has_category = has_category_folder(url)
                    if has_category:
                        docs_with_category_folder += 1
                    else:
                        docs_without_category_folder += 1
                
                logger.info(f"[CLAIM_UPDATE] Saved document {idx + 1}: filename={doc.get('filename')}, category={category}, has_category_folder={has_category_folder(url) if url else 'N/A'}")
            
            logger.info(f"[CLAIM_UPDATE] Folder structure summary:")
            logger.info(f"  - Documents with category folders: {docs_with_category_folder}")
            logger.info(f"  - Documents without category folders (backward compatible): {docs_without_category_folder}")
        except ImportError:
            # Fallback if document_utils not available
            for idx, doc in enumerate(saved_docs):
                logger.info(f"[CLAIM_UPDATE] Saved document {idx + 1}: filename={doc.get('filename')}, url={doc.get('url', '')[:50]}...")
    
    return {'modified_count': res.modified_count}


@router.delete('/application/{app_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim_application(request: Request, app_id: str):
    """Delete a claim application from MongoDB"""
    db = request.app.mongodb
    coll = db.get_collection('claims')
    # Query using string _id directly (no ObjectId conversion)
    res = await coll.delete_one({'_id': app_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Claim application not found')
    return {}

