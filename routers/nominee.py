from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/nominees", tags=["Nominees"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_nominee(nominee: schemas.NomineeCreate, db: Session = Depends(get_db)):
    nominee_id = crud.create_entry(db, models.Nominee, nominee, return_id=True)
    return {"nominee_id": nominee_id}

@router.get("/", response_model=list[schemas.Nominee])
def read_nominees(db: Session = Depends(get_db)):
    nominees = crud.get_all(db, models.Nominee)
    return [{"nomineeId": n.id,
             "userId": n.userId,
             "policyId": n.policyId,
             "name": n.name,
             "relationship": getattr(n, 'relationship_type', None),
             "phone": n.phone,
             "email": n.email} for n in nominees]

@router.get("/{nominee_id}", response_model=schemas.Nominee)
def read_nominee(nominee_id: int, db: Session = Depends(get_db)):
    nominee = crud.get_by_id(db, models.Nominee, "id", nominee_id)
    if not nominee:
        raise HTTPException(status_code=404, detail="Nominee not found")
    return {"nomineeId": nominee.id,
            "userId": nominee.userId,
            "policyId": nominee.policyId,
            "name": nominee.name,
            "relationship": getattr(nominee, 'relationship_type', None),
            "phone": nominee.phone,
            "email": nominee.email}

@router.delete("/{nominee_id}")
def delete_nominee(nominee_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Nominee, "id", nominee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Nominee not found")
    return {"message": "Nominee deleted successfully"}

@router.put("/{nominee_id}")
def update_nominee(nominee_id: int, nominee: schemas.NomineeUpdate, db: Session = Depends(get_db)):
    success = crud.update_by_id(db, models.Nominee, "id", nominee_id, nominee)
    if not success:
        raise HTTPException(status_code=404, detail="Nominee not found")
    return {"message": "Nominee updated successfully"}