from fastapi import APIRouter, Request, HTTPException
from fastapi import status
from bson import ObjectId
from datetime import datetime
from typing import List
import schemas_mongo as schemas
from mongo import get_collection

# local DB access to create SQL Policy when requested
from database import SessionLocal
import crud, models
import requests
import os

AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "http://localhost:8001")

router = APIRouter(prefix="/life-insurance", tags=["life_insurance"])


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


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_application(request: Request, payload: dict):
    """
    Accept a flexible JSON payload for life insurance applications.
    Using a plain `dict` here avoids FastAPI/Pydantic 422 validation when the
    frontend sends camelCase or slightly different shapes. We still set
    timestamps and persist whatever JSON the client provided.
    """
    db = request.app.mongodb
    coll = db.get_collection('life_insurance_applications')
    # ensure we have a mutable dict
    doc = dict(payload or {})
    # Generate a string id upfront
    doc_id = str(ObjectId())
    doc['_id'] = doc_id

    # Optionally create a SQL Policy if the client provided a `policy` object
    # or `policy` key contains a dict with policy fields. After creating
    # the SQL record we will store its id in the Mongo document under `policy`.
    try:
        policy_obj = doc.get('policy')
        if isinstance(policy_obj, dict):
            db = SessionLocal()
            try:
                # build a minimal policy payload; ensure required JSON fields exist
                policy_payload = {
                    "userId": doc.get('user_id') or doc.get('userId'),
                    "type": policy_obj.get('type', 'life_insurance'),
                    "planName": policy_obj.get('planName', policy_obj.get('plan_name', 'Life Plan')),
                    "policyNumber": policy_obj.get('policyNumber') or ("LIF" + datetime.utcnow().strftime("%Y%m%d%H%M%S")),
                    "coverage": policy_obj.get('coverage', policy_obj.get('coverage_amount', 0.0)) or 0.0,
                    "premium": policy_obj.get('premium', 0.0) or 0.0,
                    "status": policy_obj.get('status', 'Active'),  # Ensure status is always set
                    # personalDetails is non-null in the Policy model, provide at least an empty dict
                    "personalDetails": policy_obj.get('personalDetails') or doc.get('personal_details') or {},
                    "policyDocument": policy_obj.get('policyDocument') or policy_obj.get('policy_document') or None,
                    "startDate": policy_obj.get('startDate'),
                    "expiryDate": policy_obj.get('expiryDate'),
                    "benefits": policy_obj.get('benefits'),
                    "nominee": policy_obj.get('nominee'),
                    "nomineeId": policy_obj.get('nomineeId'),
                    "applicationId": doc_id # Store the Mongo ID in SQL
                }
                
                # Ensure doc has the policyNumber IMMEDIATELY so it's returned even if SQL creation fails
                doc['policyNumber'] = policy_payload.get("policyNumber")

                # create the Policy SQL row and get its id
                policy_id = crud.create_entry(db, models.Policy, policy_payload, return_id=True)
                # store numeric id and policyNumber in the Mongo document
                # store numeric id and policyNumber in the Mongo document
                doc['policy'] = policy_id
                
            finally:
                # NEW: Create a SQL Payment record if payment details exist in the doc
                try:
                    payment_info = doc.get('payment')
                    if payment_info and isinstance(payment_info, dict):
                         # Safely get policy_id if it exists
                         safe_policy_id = locals().get('policy_id')
                         
                         # Handle userId conversion safely
                         raw_user_id = doc.get('user_id') or doc.get('userId')
                         safe_user_id = None
                         if raw_user_id and str(raw_user_id).isdigit():
                             safe_user_id = int(raw_user_id)
                         
                         # Prepare payment payload
                         payment_payload = {
                             "userId": safe_user_id,
                             "policyId": safe_policy_id, 
                             "policyNumber": policy_payload.get("policyNumber") if 'policy_payload' in locals() else None,
                             "applicationId": doc_id,
                             "amount": policy_payload.get("premium", 0.0) if 'policy_payload' in locals() else 0.0,
                             "paymentMethod": payment_info.get('method', 'unknown'),
                             "status": 'success', 
                             "orderId": f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{doc_id[-4:]}",
                             "transactionId": f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{doc_id[-4:]}",
                             "paidDate": datetime.utcnow().date(),
                             "returnUrl": "http://localhost:3000/dashboard", 
                             "paymentUrl": "http://localhost:3000/pay" 
                         }
                         
                         print(f"Creating SQL Payment record for App ID {doc_id}...")
                         crud.create_entry(db, models.Payments, payment_payload)
                         print("SQL Payment record created successfully.")

                except Exception as e:
                    import logging
                    logging.exception(f"Failed to create SQL Payment for App ID {doc_id}: {e}")
                
                db.close()
    except Exception:
        # don't fail the whole application creation if policy creation fails;
        # log and continue with the application record (the caller can retry)
        import logging
        logging.exception('Failed to create SQL policy from life-insurance payload')

    now = datetime.utcnow()
    # only set timestamps if not provided
    doc.setdefault('created_at', now)
    doc['updated_at'] = now
    
    await coll.insert_one(doc)

    # -------------------------------------------------------------
    # NEW: Trigger Agent Workflow & Create ApplicationProcess Entry
    # -------------------------------------------------------------
    try:
        sql_db = SessionLocal()
        try:
            # Create the tracking entry for the Admin Panel
            process_data = {
                "applicationId": doc_id,
                "status": "Submitted", # Initial status
                "currentStep": "ingest",
                "startTime": datetime.utcnow().date(),
                "lastUpdated": datetime.utcnow().date(),
                "customerId": doc.get('user_id') or doc.get('userId'), # Ensure this maps to a valid User ID if possible
                "agentData": {},
                "stepHistory": []
            }
            crud.create_entry(sql_db, models.ApplicationProcess, process_data)
        except Exception as e:
            import logging
            logging.error(f"Failed to create ApplicationProcess entry: {e}")
        finally:
            sql_db.close()

        # Trigger the Agent
        try:
             # Fire and forget (or short timeout) to avoid blocking response
            requests.post(
                f"{AGENT_SERVER_URL}/underwrite", 
                json={"application_id": doc_id}, 
                timeout=2
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to trigger Agent Server: {e}")
            
    except Exception as e:
         import logging
         logging.error(f"Agent trigger block failed: {e}")



    # Return the doc_id and the generated policyNumber
    return {
        'id': doc_id, 
        'policyNumber': doc.get('policyNumber')
    }


@router.get('/user/{user_id}', response_model=List[dict])
async def get_applications_for_user(request: Request, user_id: str):
    db = request.app.mongodb
    coll = db.get_collection('life_insurance_applications')
    cursor = coll.find({'user_id': user_id}).sort('created_at', -1)
    results = [ _oid_str(d) async for d in cursor ]
    return results


@router.get('/{app_id}')
async def get_application(request: Request, app_id: str):
    db = request.app.mongodb
    coll = db.get_collection('life_insurance_applications')
    # Query using string _id directly (no ObjectId conversion)
    doc = await coll.find_one({'_id': app_id})
    if not doc:
        raise HTTPException(status_code=404, detail='Not found')
    return _oid_str(doc)


@router.patch('/{app_id}')
async def update_application(request: Request, app_id: str, payload: dict):
    db = request.app.mongodb
    coll = db.get_collection('life_insurance_applications')
    # Query using string _id directly (no ObjectId conversion)
    payload['updated_at'] = datetime.utcnow()
    res = await coll.update_one({'_id': app_id}, {'$set': payload})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Not found')
    return {'modified_count': res.modified_count}


@router.delete('/{app_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(request: Request, app_id: str):
    db = request.app.mongodb
    coll = db.get_collection('life_insurance_applications')
    # Query using string _id directly (no ObjectId conversion)
    res = await coll.delete_one({'_id': app_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Not found')
    return {}
