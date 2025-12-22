from fastapi import FastAPI
from database import engine, Base
from routers import users, policy, claims, products, contact, quotation, documents, nominee, activities, notifications, payments
from models import *

app = FastAPI(title="Insurance Management Backend")

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(policy.router)
app.include_router(claims.router)
app.include_router(products.router)
app.include_router(contact.router)
app.include_router(quotation.router)
app.include_router(documents.router)
app.include_router(nominee.router)
app.include_router(activities.router)
app.include_router(notifications.router)
app.include_router(payments.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Insurance Management API"}
