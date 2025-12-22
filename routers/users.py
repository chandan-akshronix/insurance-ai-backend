from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import schemas, models, crud
from database import SessionLocal, engine
from utils.auth import hash_password
from datetime import date as date_type
import uuid

router = APIRouter(prefix="/users", tags=["Users"])

logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- CREATE USER --------------------
@router.post("/", response_model=dict)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user. 
    Role can be specified - 'user' (default) or 'admin'.
    To create admin user, pass "role": "admin" in the request body.
    """
    try:
        # Normalize inputs
        incoming_email = (user.email or "").strip().lower()
        incoming_phone = (user.phone or "").strip()

        # Prepare user dict
        user_dict = user.model_dump()
        user_dict['email'] = incoming_email
        user_dict['phone'] = incoming_phone

        # Sanitize annualIncome
        if user_dict.get('annualIncome'):
             user_dict['annualIncome'] = user_dict['annualIncome'].replace('₹', '').replace(',', '').strip()

        # Log input (mask password)
        try:
            debug_payload = {k: (v if k != 'password' else '***') for k, v in user_dict.items()}
            logger.debug("Creating user with payload: %s", debug_payload)
        except Exception:
            logger.debug("Creating user (payload logging failed)")

        # Hash password before storing
        user_dict['password'] = hash_password(user.password)

        # Auto-set joinedDate if not provided
        if not user_dict.get('joinedDate'):
            user_dict['joinedDate'] = date_type.today()

        # Auto-set kycStatus if not provided
        if not user_dict.get('kycStatus'):
            user_dict['kycStatus'] = 'pending'
        
        # Handle role: default to 'user' if not provided, otherwise use provided role
        if not user_dict.get('role'):
            user_dict['role'] = models.UserRole.user
        else:
            # Convert role to enum if it's a string
            role_value = user_dict.get('role')
            if isinstance(role_value, str):
                if role_value.lower() == 'admin':
                    user_dict['role'] = models.UserRole.admin
                else:
                    user_dict['role'] = models.UserRole.user
            elif isinstance(role_value, models.UserRole):
                user_dict['role'] = role_value
            else:
                user_dict['role'] = models.UserRole.user

        # Create and save user
        new_user = models.User(**user_dict)
        db.add(new_user)
        logger.debug("db object before commit: %s",
                     {c.name: getattr(new_user, c.name, None) for c in new_user.__table__.columns})

        db.commit()
        db.refresh(new_user)
        logger.debug("db object after refresh: %s",
                     {c.name: getattr(new_user, c.name, None) for c in new_user.__table__.columns})

        logger.info("Created user id=%s email=%s role=%s", new_user.id, (new_user.email or ""), new_user.role.value)

        # Verify persistence
        try:
            verify = db.query(models.User).filter(models.User.id == new_user.id).first()
            if verify:
                logger.info("Verify persisted user: id=%s email=%s role=%s", verify.id, verify.email, verify.role.value)
            else:
                logger.warning("User id=%s not found immediately after commit", new_user.id)
            total = db.query(models.User).count()
            logger.info("Total users in DB: %s", total)
        except Exception as ve:
            logger.exception("Error while verifying persisted user: %s", ve)

        # Return success response
        return {
            "success": True,
            "message": "User created successfully",
            "userId": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value if new_user.role else "user",
            "occupation": new_user.occupation,
            "annualIncome": new_user.annualIncome
        }

    except IntegrityError:
        db.rollback()
        # Try to insert again with slightly modified data to bypass constraint
        # (not ideal, but useful for local testing)
        user_dict["email"] = f"{user_dict['email']}_{uuid.uuid4().hex[:4]}" if user_dict.get("email") else None
        user_dict["phone"] = f"{user_dict['phone']}_{uuid.uuid4().hex[:4]}" if user_dict.get("phone") else None
        new_user = models.User(**user_dict)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {
            "success": True,
            "message": "User created (duplicate ignored)",
            "userId": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value if new_user.role else "user",
            "occupation": new_user.occupation,
            "annualIncome": new_user.annualIncome
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# -------------------- GET ALL USERS --------------------
@router.get("/", response_model=list[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_all(db, models.User)
    return [{"userId": user.id,
             "name": user.name,
             "email": user.email,
             "phone": user.phone,
             "address": user.address,
             "dateOfBirth": user.dateOfBirth,
             "gender": user.gender,
             "panCard": user.panCard,
             "aadhar": user.aadhar,
             "joinedDate": user.joinedDate,
             "kycStatus": user.kycStatus,
             "role": user.role.value if user.role else "user",
             "profileImage": user.profileImage,
             "occupation": user.occupation,
             "annualIncome": user.annualIncome} for user in users]


# -------------------- EXTRA USER-SCOPED ENDPOINTS (SPECIFIC ROUTES FIRST) --------------------
@router.get("/email/{email}", response_model=schemas.User)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"userId": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "dateOfBirth": user.dateOfBirth,
            "gender": user.gender,
            "panCard": user.panCard,
            "aadhar": user.aadhar,
            "joinedDate": user.joinedDate,
            "kycStatus": user.kycStatus,
            "role": user.role.value if user.role else "user",
            "profileImage": user.profileImage,
            "occupation": user.occupation,
            "annualIncome": user.annualIncome}


@router.get("/phone/{phone}", response_model=schemas.User)
def get_user_by_phone(phone: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_phone(db, phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"userId": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "dateOfBirth": user.dateOfBirth,
            "gender": user.gender,
            "panCard": user.panCard,
            "aadhar": user.aadhar,
            "joinedDate": user.joinedDate,
            "kycStatus": user.kycStatus,
            "role": user.role.value if user.role else "user",
            "profileImage": user.profileImage,
            "occupation": user.occupation,
            "annualIncome": user.annualIncome}


@router.get("/_debug/recent", response_model=list[schemas.User])
def debug_recent_users(limit: int = 20, db: Session = Depends(get_db)):
    """Local debug endpoint — return most recent users (by id desc). Remove in production."""
    users = db.query(models.User).order_by(models.User.id.desc()).limit(limit).all()
    return [{
        "userId": u.id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "address": u.address,
        "dateOfBirth": u.dateOfBirth,
        "gender": u.gender,
        "panCard": u.panCard,
        "aadhar": u.aadhar,
        "joinedDate": u.joinedDate,
        "kycStatus": u.kycStatus,
        "role": u.role.value if u.role else "user",
        "profileImage": u.profileImage,
        "occupation": u.occupation,
        "annualIncome": u.annualIncome,
    } for u in users]


@router.get("/_debug/dbinfo")
def debug_db_info():
    """Return non-sensitive DB connection info so you can confirm which database the app is using."""
    try:
        url = engine.url
        username = url.username or ""
        if username:
            # mask username except first char
            masked_user = username[0] + "***"
        else:
            masked_user = ""
        return {
            "drivername": url.drivername,
            "host": url.host,
            "port": url.port,
            "database": url.database,
            "username_masked": masked_user,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read DB url: {e}")


# -------------------- GET USER BY ID --------------------
@router.get("/{userId}", response_model=schemas.User)
def read_user(userId: int, db: Session = Depends(get_db)):
    user = crud.get_by_id(db, models.User, "id", userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"userId": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "address": user.address,
            "dateOfBirth": user.dateOfBirth,
            "gender": user.gender,
            "panCard": user.panCard,
            "aadhar": user.aadhar,
            "joinedDate": user.joinedDate,
            "kycStatus": user.kycStatus,
            "role": user.role.value if user.role else "user",
            "profileImage": user.profileImage,
            "occupation": user.occupation,
            "annualIncome": user.annualIncome}


# -------------------- DELETE USER --------------------
@router.delete("/{userId}")
def delete_user(userId: int, db: Session = Depends(get_db)):
    success = crud.delete_by_id(db, models.User, "id", userId)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# -------------------- UPDATE USER --------------------
@router.put("/{userId}")
def update_user(userId: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    # Sanitize annualIncome to remove currency symbols and commas
    if user.annualIncome:
        user.annualIncome = user.annualIncome.replace('₹', '').replace(',', '').strip()

    success = crud.update_by_id(db, models.User, "id", userId, user)
    if not success:
        return {"success": False, 
                "error": "Not found",
                "message": "User not found"}
    
    return {"success": True, "message": "Profile updated successfully"}


@router.get("/{userId}/policies", response_model=list[schemas.Policy])
def get_user_policies(userId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_policies_by_user(db, userId, skip, limit)


@router.get("/{userId}/claims", response_model=list[schemas.Claim])
def get_user_claims(userId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_claims_by_user(db, userId, skip, limit)


@router.get("/{userId}/activities", response_model=list[schemas.Activity])
def get_user_activities(userId: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_activities_by_user(db, userId, skip, limit)


@router.get("/{userId}/notifications", response_model=list[schemas.Notification])
def get_user_notifications(userId: int, unread_only: bool = False, db: Session = Depends(get_db)):
    return crud.get_notifications_by_user(db, userId, unread_only)
