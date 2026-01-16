
from database import SessionLocal
import models
import crud
from datetime import datetime

def debug_payment_creation():
    print("DEBUG: Attempting to create Payment record directly...")
    db = SessionLocal()
    try:
        # Check if user exists
        user_id = 1
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            print(f"WARNING: User with ID {user_id} does not exist! creating one for testing...")
            # Create a dummy user
            user = models.User(name="Test User", password="hashed_password", email="test@example.com", joinedDate=datetime.utcnow().date())
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created temporary user with ID: {user.id}")
            user_id = user.id
        else:
            print(f"Found existing user with ID {user_id}")

        # Check if policy exists (or create one)
        # For this test, we can try with policyId=None first as it is nullable
        policy_id = None
        
        # Payload mimicking routers/life_insurance.py
        payment_payload = {
             "userId": user_id,
             "policyId": policy_id, 
             "policyNumber": "TEST-POL-DEBUG",
             "applicationId": "test_mongo_id_123",
             "amount": 1000.0,
             "paymentMethod": "upi",
             "status": "success", 
             "orderId": f"ORD-DEBUG-{datetime.utcnow().strftime('%H%M%S')}",
             "transactionId": f"TXN-DEBUG-{datetime.utcnow().strftime('%H%M%S')}",
             "paidDate": datetime.utcnow().date(),
             "returnUrl": "http://localhost:3000/dashboard", 
             "paymentUrl": "http://localhost:3000/pay" 
        }
        
        print("Calling crud.create_entry...")
        payment = crud.create_entry(db, models.Payments, payment_payload)
        print("SUCCESS! Payment created.")
        print(f"Payment ID: {payment.id}")
        
    except Exception as e:
        print("\n!!! ERROR CAUGHT !!!")
        print(e)
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_payment_creation()
