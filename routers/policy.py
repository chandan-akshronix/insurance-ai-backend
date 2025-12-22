from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal
from datetime import datetime
import random, string

router = APIRouter(prefix="/policy", tags=["Policy"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_policy(policy: schemas.PolicyCreate, db: Session = Depends(get_db)):
    # Create a Policy record. PolicyCreate includes userId per schema.
    policy_obj = crud.create_entry(db, models.Policy, policy)
    return {
        "policyId": policy_obj.id,
        "userId": getattr(policy_obj, "userId", None),
        "type": policy_obj.type,
        "planName": policy_obj.planName,
        "policyNumber": policy_obj.policyNumber,
        "coverage": policy_obj.coverage,
        "premium": policy_obj.premium,
        "status": policy_obj.status,
        "startDate": policy_obj.startDate,
        "expiryDate": policy_obj.expiryDate,
        "benefits": policy_obj.benefits,
        "nominee": policy_obj.nominee,
        "nomineeId": policy_obj.nomineeId,
        "policyDocument": policy_obj.policyDocument,
    }

@router.get("/", response_model=list[schemas.Policy])
def read_policies(db: Session = Depends(get_db)):
    policies = crud.get_all(db, models.Policy)
    return [{"policyId": p.id,
             "userId": getattr(p, "userId", None),
             "type": p.type,
             "planName": p.planName,
             "policyNumber": p.policyNumber,
             "coverage": p.coverage,
             "premium": p.premium,
             "tenure": getattr(p, "tenure", None),
             "startDate": p.startDate,
             "expiryDate": p.expiryDate,
             "benefits": p.benefits,
             "nominee": p.nominee,
             "nomineeId": p.nomineeId,
             "policyDocument": p.policyDocument} for p in policies]


@router.get("/user/{user_id}", response_model=list[schemas.Policy])
def get_policies_by_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    policies = crud.get_policies_by_user(db, user_id, skip, limit)
    return [{"policyId": p.id,
             "userId": getattr(p, "userId", None),
             "type": p.type,
             "planName": p.planName,
             "policyNumber": p.policyNumber,
             "coverage": p.coverage,
             "premium": p.premium,
             "tenure": getattr(p, "tenure", None),
             "startDate": p.startDate,
             "expiryDate": p.expiryDate,
             "benefits": p.benefits,
             "nominee": p.nominee,
             "nomineeId": p.nomineeId,
             "policyDocument": p.policyDocument} for p in policies]


@router.get("/type/{policy_type}", response_model=list[schemas.Policy])
def get_policies_by_type(policy_type: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    policies = crud.get_policies_by_type(db, policy_type, skip, limit)
    return [{"policyId": p.id,
             "userId": getattr(p, "userId", None),
             "type": p.type,
             "planName": p.planName,
             "policyNumber": p.policyNumber,
             "coverage": p.coverage,
             "premium": p.premium,
             "tenure": getattr(p, "tenure", None),
             "startDate": p.startDate,
             "expiryDate": p.expiryDate,
             "benefits": p.benefits,
             "nominee": p.nominee,
             "nomineeId": p.nomineeId,
             "policyDocument": p.policyDocument} for p in policies]


@router.get("/number/{policy_number}", response_model=schemas.Policy)
def get_policy_by_number(policy_number: str, db: Session = Depends(get_db)):
    policy = crud.get_policy_by_number(db, policy_number)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policyId": policy.id,
            "userId": getattr(policy, "userId", None),
            "type": policy.type,
            "planName": policy.planName,
            "policyNumber": policy.policyNumber,
            "coverage": policy.coverage,
            "premium": policy.premium,
            "status": policy.status,
            "startDate": policy.startDate,
            "expiryDate": policy.expiryDate,
            "benefits": policy.benefits,
            "nominee": policy.nominee,
            "nomineeId": policy.nomineeId,
            "policyDocument": policy.policyDocument,}

@router.get("/{policy_id}", response_model=schemas.Policy)
def read_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = crud.get_by_id(db, models.Policy, "id", policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"policyId": policy.id,
            "userId": getattr(policy, "userId", None),
            "type": policy.type,
            "planName": policy.planName,
            "policyNumber": policy.policyNumber,
            "coverage": policy.coverage,
            "premium": policy.premium,
            "status": policy.status,
            "startDate": policy.startDate,
            "expiryDate": policy.expiryDate,
            "benefits": policy.benefits,
            "nominee": policy.nominee,
            "nomineeId": policy.nomineeId,
            "policyDocument": policy.policyDocument,}

@router.delete("/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Policy, "id", policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy deleted successfully"}

@router.put("/{policy_id}")
def update_policy(policy_id: int, policy: schemas.PolicyUpdate, db: Session = Depends(get_db)):
    success = crud.update_by_id(db, models.Policy, "id", policy_id, policy)
    if not success:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"success": True,
            "message": "Policy updated successfully"}


# -------------------- PURCHASE POLICY --------------------
@router.post("/purchase")
def purchase_policy(policy: schemas.PolicyPurchaseCreate, db: Session = Depends(get_db)):
    """
    Create a new policy purchase entry with auto-generated policy number.
    """
    # Generate unique policy number (timestamp + 4 random digits)
    policy_number = "POL" + datetime.now().strftime("%Y%m%d%H%M%S") + ''.join(random.choices(string.digits, k=4))

    # Prepare data for insertion (match column names in models)
    # Normalize personalDetails from Pydantic v2/v1 or plain dict
    pd = getattr(policy, "personalDetails", None)
    if pd:
        if hasattr(pd, "model_dump"):
            pd_payload = pd.model_dump()
        elif hasattr(pd, "dict"):
            pd_payload = pd.dict()
        else:
            pd_payload = pd
    else:
        pd_payload = {}

    policy_data = {
        "userId": getattr(policy, "userId", None),
        "type": policy.type,
        "planName": policy.planName,
        "coverage": policy.coverage,
        "premium": policy.premium,
        "tenure": policy.tenure,
        "nominee": policy.nominee,
        "nomineeId": policy.nomineeId,
        "personalDetails": pd_payload,
        "policyNumber": policy_number
    }

    try:
        # ✅ directly use the dictionary
        policy_id = crud.create_entry(db, models.PolicyPurchase, policy_data, return_id=True)

        return {
            "success": True,
            "policyId": policy_id,
            "policyNumber": policy_number,
            "message": "Policy purchased successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error purchasing policy: {str(e)}")
