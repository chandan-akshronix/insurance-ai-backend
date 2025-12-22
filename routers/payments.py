from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas, models, crud
from database import SessionLocal

router = APIRouter(prefix="/payments", tags=["Payments"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    payment_obj = crud.create_entry(db, models.Payments, payment)
    return {"success": True,
            "paymentId": getattr(payment_obj, 'id', None),
            "orderId": getattr(payment_obj, 'orderId', None),
            "amount": getattr(payment_obj, 'amount', None),
            "paymentUrl": getattr(payment_obj, 'paymentUrl', None)
            }

@router.get("/", response_model=list[schemas.Payment])
def read_payments(db: Session = Depends(get_db)):
    payments = crud.get_all(db, models.Payments)
    return [{"paymentId": p.id,
             "userId": getattr(p, "userId", None),
             "policyId": getattr(p, "policyId", None),
             "amount": p.amount,
             "orderId": getattr(p, "orderId", None),
             "paidDate": p.paidDate,
             "paymentMethod": getattr(p, "paymentMethod", None),
             "status": p.status,
             "transactionId": getattr(p, "transactionId", None),
             "returnUrl": getattr(p, "returnUrl", None),
             "paymentUrl": getattr(p, "paymentUrl", None)} for p in payments]

@router.get("/{payment_id}", response_model=schemas.Payment)
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = crud.get_by_id(db, models.Payments, "id", payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"paymentId": payment.id,
            "userId": getattr(payment, "userId", None),
            "policyId": getattr(payment, "policyId", None),
            "amount": payment.amount,
            "orderId": getattr(payment, "orderId", None),
            "paidDate": payment.paidDate,
            "paymentMethod": getattr(payment, "paymentMethod", None),
            "status": payment.status,
            "transactionId": getattr(payment, "transactionId", None),
            "returnUrl": getattr(payment, "returnUrl", None),
            "paymentUrl": getattr(payment, "paymentUrl", None)}


@router.get("/policy/{policy_id}", response_model=list[schemas.Payment])
def get_payments_by_policy(policy_id: int, db: Session = Depends(get_db)):
    payments = crud.get_payments_by_policy(db, policy_id)
    return [{"paymentId": p.id,
             "userId": getattr(p, "userId", None),
             "policyId": getattr(p, "policyId", None),
             "amount": p.amount,
             "orderId": getattr(p, "orderId", None),
             "paidDate": p.paidDate,
             "paymentMethod": getattr(p, "paymentMethod", None),
             "status": p.status,
             "transactionId": getattr(p, "transactionId", None),
             "returnUrl": getattr(p, "returnUrl", None),
             "paymentUrl": getattr(p, "paymentUrl", None)} for p in payments]


@router.get("/user/{user_id}", response_model=list[schemas.Payment])
def get_payments_by_user(user_id: int, db: Session = Depends(get_db)):
    payments = crud.get_payments_by_user(db, user_id)
    return [{"paymentId": p.id,
             "userId": getattr(p, "userId", None),
             "policyId": getattr(p, "policyId", None),
             "amount": p.amount,
             "orderId": getattr(p, "orderId", None),
             "paidDate": p.paidDate,
             "paymentMethod": getattr(p, "paymentMethod", None),
             "status": p.status,
             "transactionId": getattr(p, "transactionId", None),
             "returnUrl": getattr(p, "returnUrl", None),
             "paymentUrl": getattr(p, "paymentUrl", None)} for p in payments]


@router.get("/history/{user_id}", response_model=list[schemas.Payment])
def get_payment_history(user_id: int, db: Session = Depends(get_db)):
    payments = crud.get_payments_by_user(db, user_id)
    return [{"paymentId": p.id,
             "userId": getattr(p, "userId", None),
             "policyId": getattr(p, "policyId", None),
             "amount": p.amount,
             "orderId": getattr(p, "orderId", None),
             "paidDate": p.paidDate,
             "paymentMethod": getattr(p, "paymentMethod", None),
             "status": p.status,
             "transactionId": getattr(p, "transactionId", None),
             "returnUrl": getattr(p, "returnUrl", None),
             "paymentUrl": getattr(p, "paymentUrl", None)} for p in payments]