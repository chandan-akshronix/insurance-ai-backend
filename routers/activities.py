from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/activities", tags=["Activities"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    # Use correct model reference (models.Activities) and return created object
    activity_obj = crud.create_entry(db, models.Activities, activity)
    return {"success": True,
            "message": "Activity created successfully",
            "activity_id": getattr(activity_obj, 'id', None)}

@router.get("/", response_model=list[schemas.Activity])
def read_activities(db: Session = Depends(get_db)):
    activities = crud.get_all(db, models.Activities)
    return [{"activityId": a.id,
             "userId": getattr(a, 'userId', None),
             "type": a.type,
             "description": a.description,
             "time": a.time,
             "amount": a.amount} for a in activities]

@router.get("/{activity_id}", response_model=schemas.Activity)
def read_activity(activity_id: int, db: Session = Depends(get_db)):
    activity = crud.get_by_id(db, models.Activities, "id", activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"activityId": activity.id,
            "userId": getattr(activity, 'userId', None),
            "type": activity.type,
            "description": activity.description,
            "time": activity.time,
            "amount": activity.amount}


@router.get("/user/{user_id}", response_model=list[schemas.Activity])
def get_activities_by_user(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    activities = crud.get_activities_by_user(db, user_id, skip, limit)
    return [{"activityId": a.id,
             "userId": getattr(a, 'userId', None),
             "type": a.type,
             "description": a.description,
             "time": a.time,
             "amount": a.amount} for a in activities]


@router.get("/user/{user_id}/type/{activity_type}", response_model=list[schemas.Activity])
def get_activities_by_type(user_id: int, activity_type: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    activities = crud.get_activities_by_type(db, activity_type, user_id, skip, limit)
    return [{"activityId": a.id,
             "userId": getattr(a, 'userId', None),
             "type": a.type,
             "description": a.description,
             "time": a.time,
             "amount": a.amount} for a in activities]