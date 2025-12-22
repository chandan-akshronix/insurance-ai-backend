from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/claims", tags=["Claims"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_claim(claim: schemas.ClaimCreate, db: Session = Depends(get_db)):
    claim_id = crud.create_entry(db, models.Claim, claim, return_id=True)
    return {"claim_id": claim_id}

@router.get("/", response_model=list[schemas.Claim])
def read_claims(db: Session = Depends(get_db)):
    # Support pagination
    claims = crud.get_all(db, models.Claim)
    return [{"claimId": c.id,
             "userId": c.userId,
             "policyId": c.policyId,
             "claimType": c.claimType,
             "amount": c.amount,
             "status": c.status} for c in claims]


@router.get("/user/{user_id}", response_model=list[schemas.Claim])
def get_claims_by_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    claims = crud.get_claims_by_user(db, user_id, skip, limit)
    return [{"claimId": c.id,
             "userId": c.userId,
             "policyId": c.policyId,
             "claimType": c.claimType,
             "amount": c.amount,
             "status": c.status} for c in claims]


@router.get("/policy/{policy_id}", response_model=list[schemas.Claim])
def get_claims_by_policy(policy_id: int, db: Session = Depends(get_db)):
    claims = crud.get_claims_by_policy(db, policy_id)
    return [{"claimId": c.id,
             "userId": c.userId,
             "policyId": c.policyId,
             "claimType": c.claimType,
             "amount": c.amount,
             "status": c.status} for c in claims]


@router.get("/status/{status}", response_model=list[schemas.Claim])
def get_claims_by_status(status: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    claims = crud.get_claims_by_status(db, status, skip, limit)
    return [{"claimId": c.id,
             "userId": c.userId,
             "policyId": c.policyId,
             "claimType": c.claimType,
             "amount": c.amount,
             "status": c.status} for c in claims]

@router.get("/{claim_id}", response_model=schemas.Claim)
def read_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = crud.get_by_id(db, models.Claim, "id", claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"claimId": claim.id,
            "userId": claim.userId,
            "policyId": claim.policyId,
            "claimType": claim.claimType,
            "amount": claim.amount,
            "status": claim.status}

@router.delete("/{claim_id}")
def delete_claim(claim_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Claim, "id", claim_id)
    if not success:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim deleted successfully", "status_code": 200}

@router.put("/{claim_id}")
def update_claim(claim_id: int, claim: schemas.ClaimUpdate, db: Session = Depends(get_db)):
    success = crud.update_by_id(db, models.Claim, "id", claim_id, claim)
    if not success:
        raise HTTPException(status_code=404, detail="Claim not found")
    return {"message": "Claim updated successfully"}