from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/contact", tags=["Contact"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    contact_id = crud.create_entry(db, models.Contact, contact, return_id=True)
    return {"contact_id": contact_id}

@router.get("/", response_model=list[schemas.Contact])
def read_contacts(db: Session = Depends(get_db)):
    contacts = crud.get_all(db, models.Contact)
    return [{"contactId": c.id,
             "fullName": c.fullName,
             "phone": c.phone,
             "email": c.email,
             "category": c.category,
             "message": c.message} for c in contacts]

@router.get("/{contact_id}", response_model=schemas.Contact)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_by_id(db, models.Contact, "id", contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"contactId": contact.id,
            "fullName": contact.fullName,
            "phone": contact.phone,
            "email": contact.email,
            "category": contact.category,
            "message": contact.message}

@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.Contact, "id", contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

@router.put("/{contact_id}")
def update_contact(contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends   (get_db)):
    success = crud.update_by_id(db, models.Contact, "id", contact_id, contact)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact updated successfully"}