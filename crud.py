from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
from typing import Any, Dict, Optional, List


def _to_dict(data: Any) -> Dict:
    """Convert Pydantic model or dict-like into plain dict."""
    if data is None:
        return {}
    # Pydantic v2 uses model_dump(), v1 used dict()
    if hasattr(data, "model_dump"):
        try:
            return data.model_dump()
        except Exception:
            pass
    if hasattr(data, "dict"):
        # Pydantic v1 BaseModel or other dict-like
        try:
            return data.dict()
        except Exception:
            pass
    if isinstance(data, dict):
        return data
    # Fallback: try to use __dict__
    return getattr(data, "__dict__", {})


def create_entry(db: Session, model, data: Any, return_id: bool = False):
    """Create a model instance from a Pydantic model or dict.

    Returns the created ORM object or primary key value when return_id=True.
    """
    payload = _to_dict(data)
    db_obj = model(**payload)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)

    if return_id:
        pk_name = [col.name for col in model.__table__.columns if col.primary_key][0]
        return getattr(db_obj, pk_name)

    return db_obj


def get_all(db: Session, model) -> List:
    return db.query(model).all()


def get_by_id(db: Session, model, id_field: str, id_value: int):
    return db.query(model).filter(getattr(model, id_field) == id_value).first()


def delete_by_id(db: Session, model, id_field: str, id_value: int) -> bool:
    entry = db.query(model).filter(getattr(model, id_field) == id_value).first()
    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False


def update_by_id(db: Session, model, id_field: str, id_value: int, data: Any):
    entry = db.query(model).filter(getattr(model, id_field) == id_value).first()
    if not entry:
        return None

    payload = _to_dict(data)
    # Only update provided keys
    for key, value in payload.items():
        if hasattr(entry, key):
            setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return entry


# ------------------ Model-specific helpers ------------------

def get_user_by_email(db: Session, email: str):
    if not email:
        return None
    # Normalize for case-insensitive match and trim whitespace
    norm = email.strip().lower()
    return db.query(models.User).filter(func.lower(models.User.email) == norm).first()


def get_user_by_phone(db: Session, phone: str):
    return db.query(models.User).filter(models.User.phone == phone).first()


# Policy-specific queries
def get_policies_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Policy).filter(models.Policy.userId == user_id).offset(skip).limit(limit).all()


def get_policies_by_type(db: Session, policy_type: str, skip: int = 0, limit: int = 100):
    return db.query(models.Policy).filter(models.Policy.type == policy_type).offset(skip).limit(limit).all()


def get_policy_by_number(db: Session, policy_number: str):
    return db.query(models.Policy).filter(models.Policy.policyNumber == policy_number).first()


# Claim-specific queries
def get_claims_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Claim).filter(models.Claim.userId == user_id).offset(skip).limit(limit).all()


def get_claims_by_policy(db: Session, policy_id: int):
    return db.query(models.Claim).filter(models.Claim.policyId == policy_id).all()


def get_claims_by_status(db: Session, status: str, skip: int = 0, limit: int = 100):
    return db.query(models.Claim).filter(models.Claim.status == status).offset(skip).limit(limit).all()


# Document-specific queries
def get_documents_by_user(db: Session, user_id: int):
    return db.query(models.Documents).filter(models.Documents.userId == user_id).all()


def get_documents_by_policy(db: Session, policy_id: int):
    return db.query(models.Documents).filter(models.Documents.policyId == policy_id).all()


# Activity-specific queries
def get_activities_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Activities).filter(models.Activities.userId == user_id).offset(skip).limit(limit).all()


def get_activities_by_type(db: Session, activity_type: str, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Activities).filter(
        models.Activities.userId == user_id,
        models.Activities.type == activity_type
    ).offset(skip).limit(limit).all()


# Notification-specific queries
def get_notifications_by_user(db: Session, user_id: int, unread_only: bool = False):
    query = db.query(models.Notification).filter(models.Notification.userId == user_id)
    if unread_only:
        query = query.filter(models.Notification.read == False)
    return query.all()


def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.userId == user_id
    ).first()
    if notification:
        notification.read = True
        db.commit()
        db.refresh(notification)
        return notification
    return None


# Payment-specific queries
def get_payments_by_policy(db: Session, policy_id: int):
    return db.query(models.Payments).filter(models.Payments.policyId == policy_id).all()


def get_payments_by_user(db: Session, user_id: int):
    # Get payments through policies
    return db.query(models.Payments).join(models.Policy).filter(models.Policy.userId == user_id).all()


# Nominee-specific queries
def get_nominees_by_user(db: Session, user_id: int):
    return db.query(models.Nominee).filter(models.Nominee.userId == user_id).all()


def get_nominees_by_policy(db: Session, policy_id: int):
    return db.query(models.Nominee).filter(models.Nominee.policyId == policy_id).all()



# Product-specific queries
def get_products_by_category(db: Session, category: str):
    return db.query(models.Product).filter(models.Product.category == category).all()


# Application Process queries (Agent Integration)
def get_application_process(db: Session, application_id: str):
    return db.query(models.ApplicationProcess).filter(models.ApplicationProcess.applicationId == application_id).first()


def list_application_processes(db: Session, status: Optional[str] = None):
    query = db.query(models.ApplicationProcess)
    if status:
        query = query.filter(models.ApplicationProcess.status == status)
    return query.all()


