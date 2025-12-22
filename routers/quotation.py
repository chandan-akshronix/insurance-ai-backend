from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/quotation", tags=["Quotations"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_quotation(quotation: schemas.QuotationCreate, db: Session = Depends(get_db)):
    quotation_id = crud.create_entry(db, models.Quotation, quotation, return_id=True)
    return {"quotation_id": quotation_id}

@router.get("/", response_model=list[schemas.Quotation])
def read_quotations(db: Session = Depends(get_db)):
    quotations = crud.get_all(db, models.Quotation)
    return [{"quotationId": q.id,
             "category": q.category,
             "fullName": q.fullName,
             "email": q.email,
             "phone": q.phone} for q in quotations]


@router.post("/request", response_model=dict)
def request_quotation(quotation: schemas.QuotationCreate, db: Session = Depends(get_db)):
    q_id = crud.create_entry(db, models.Quotation, quotation, return_id=True)
    return {"success": True, "quotationId": q_id}

@router.get("/{quotation_id}", response_model=schemas.Quotation)
def read_quotation(quotation_id: int, db: Session = Depends(get_db)):
    quotation = crud.get_by_id(db, models.Quotation, "id", quotation_id)
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"quotationId": quotation.id,
            "category": quotation.category,
            "fullName": quotation.fullName,
            "email": quotation.email,
            "phone": quotation.phone}

@router.delete("/{quotation_id}")
def delete_quotation(quotation_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Quotation, "id", quotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"message": "Quotation deleted successfully"}

@router.put("/{quotation_id}")
def update_quotation(quotation_id: int, quotation: schemas.QuotationUpdate, db: Session = Depends(get_db)):
    success = crud.update_by_id(db, models.Quotation, "id", quotation_id, quotation)
    if not success:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"message": "Quotation updated successfully"}