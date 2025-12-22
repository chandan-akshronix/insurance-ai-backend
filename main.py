from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from database import engine, Base
from routers import users, policy, claims, products, contact, quotation, documents, nominee, activities, notifications, payments, auth, public, life_insurance, agent_integration
from models import *
import os
from dotenv import load_dotenv
from mongo import connect_to_mongo, close_mongo

load_dotenv()

import logging
logger = logging.getLogger(__name__)

# Log database URL (mask password) for debugging
raw_db = os.getenv('DATABASE_URL', '')
if raw_db:
    try:
        # mask password between : and @ if present
        import re
        masked = re.sub(r':([^:@]+)@', ':****@', raw_db)
        logger.info('Using DATABASE_URL: %s', masked)
    except Exception:
        logger.info('Using DATABASE_URL (masked)')

app = FastAPI(title="Insurance Management Backend")

# Add validation error handler for better error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return detailed error messages"""
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

# CORS Configuration
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(public.router)  # Public endpoints (no auth required)
app.include_router(auth.router)  # Authentication endpoints
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
app.include_router(life_insurance.router)
app.include_router(agent_integration.router)

# Mount local uploads folder for development fallback when Azure is not configured
uploads_dir = os.path.join(os.getcwd(), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=uploads_dir), name='uploads')


@app.on_event("startup")
async def startup_events():
    # connect to MongoDB
    try:
        await connect_to_mongo(app)
    except Exception:
        logger.exception('Failed to connect to MongoDB during startup')


@app.on_event("shutdown")
async def shutdown_events():
    try:
        await close_mongo(app)
    except Exception:
        logger.exception('Failed to close MongoDB client during shutdown')

@app.get("/")
def root():
    return {"message": "Welcome to the Insurance Management API"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
