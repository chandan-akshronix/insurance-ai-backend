from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    # Use correct model reference and return created object
    notif = crud.create_entry(db, models.Notification, notification)
    return {"notificationId": getattr(notif, 'id', None),
            "userId": getattr(notif, 'userId', None),
            "message": notif.message,
            "time": notif.time,
            "type": notif.type,
            "read": notif.read,
            "policyId": notif.policyId,}

@router.get("/", response_model=list[schemas.Notification])
def read_notifications(db: Session = Depends(get_db)):
    notifs = crud.get_all(db, models.Notification)
    return [{"notificationId": n.id,
             "userId": getattr(n, 'userId', None),
             "message": n.message,
             "time": n.time,
             "type": n.type,
             "read": n.read,
             "policyId": getattr(n, 'policyId', None)} for n in notifs]

@router.get("/{notification_id}", response_model=schemas.Notification)
def read_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = crud.get_by_id(db, models.Notification, "id", notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"notificationId": notification.id,
            "userId": getattr(notification, 'userId', None),
            "message": notification.message,
            "time": notification.time,
            "type": notification.type,
            "read": notification.read,
            "policyId": notification.policyId,}


@router.get("/user/{user_id}", response_model=list[schemas.Notification])
def get_notifications_by_user(user_id: int, unread_only: bool = False, db: Session = Depends(get_db)):
    notifs = crud.get_notifications_by_user(db, user_id, unread_only)
    return [{"notificationId": n.id,
             "userId": getattr(n, 'userId', None),
             "message": n.message,
             "time": n.time,
             "type": n.type,
             "read": n.read,
             "policyId": getattr(n, 'policyId', None)} for n in notifs]


@router.put("/{notification_id}/read")
def mark_notification_as_read(notification_id: int, user_id: int, db: Session = Depends(get_db)):
    notification = crud.mark_notification_as_read(db, notification_id, user_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True, "message": "Notification marked as read"}


@router.put("/user/{user_id}/read-all")
def mark_all_notifications_as_read(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(models.Notification).filter(
        models.Notification.userId == user_id,
        models.Notification.read == False
    ).all()
    for notification in notifications:
        notification.read = True
    db.commit()
    return {"success": True, "message": f"{len(notifications)} notifications marked as read"}