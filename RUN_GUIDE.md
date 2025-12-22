# FastAPI Backend - Run Guide

## 📋 Overview

This is a FastAPI-based backend for the Insurance Management System. It uses:
- **PostgreSQL** (Azure PostgreSQL) for relational data
- **MongoDB** (Atlas) for document storage
- **Azure Blob Storage** (optional) for file uploads
- **FastAPI** with **Uvicorn** as the ASGI server

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** (Python 3.14 is being used in this project)
2. **PostgreSQL Database** (Azure PostgreSQL or local)
3. **MongoDB** (Atlas or local)
4. **Virtual Environment** (venv)

---

## 📦 Step 1: Setup Virtual Environment

### Windows (PowerShell)

```powershell
# Navigate to the backend directory
cd "D:\Project\insurance_project_demo_27-11-25\insurance-ai-frontend\Innsurance Backend Fast API"

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Windows (CMD)

```cmd
# Navigate to the backend directory
cd "D:\Project\insurance_project_demo_27-11-25\insurance-ai-frontend\Innsurance Backend Fast API"

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat
```

### Linux/Mac

```bash
# Navigate to the backend directory
cd insurance-ai-frontend/Innsurance\ Backend\ Fast\ API

# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**Note:** You should see `(venv)` in your terminal prompt when activated.

---

## 📥 Step 2: Install Dependencies

Once the virtual environment is activated, install all required packages:

```powershell
# Install all dependencies from requirements.txt
pip install -r requirements.txt
```

**Or install individually if needed:**

```powershell
pip install fastapi uvicorn[standard]
pip install sqlalchemy psycopg2
pip install python-dotenv python-multipart
pip install azure-storage-blob
pip install python-dateutil
pip install motor
pip install passlib[bcrypt]
```

---

## ⚙️ Step 3: Configure Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# PostgreSQL Database (Azure PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database_name?sslmode=require

# MongoDB (Atlas)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB=insurance_ai

# Azure Blob Storage (Optional - for file uploads)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONTAINER_NAME=uploads

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

### Default Values (if .env not provided)

The application uses these defaults if `.env` is not found:

- **DATABASE_URL:** `postgresql://dbadmin:admin%40123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require`
- **MONGO_URI:** `mongodb+srv://Abhijit:RStoKAluIWB4x1Pg@cluster0.zvgvv7n.mongodb.net/`
- **MONGO_DB:** `insurance_ai`
- **CORS_ORIGINS:** `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173`

**⚠️ Important:** Update these with your actual credentials!

---

## 🗄️ Step 4: Database Setup

### PostgreSQL Database

The application will automatically create all tables on startup using SQLAlchemy:

```python
Base.metadata.create_all(bind=engine)
```

**No manual migration needed** - tables are created automatically.

### MongoDB

MongoDB connection is handled automatically on startup. No manual setup required.

---

## ▶️ Step 5: Run the Server

### Development Mode (with auto-reload)

```powershell
# Make sure you're in the backend directory and venv is activated
uvicorn main:app --reload
```

### Production Mode

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000
```

### With Custom Port

```powershell
uvicorn main:app --reload --port 8000
```

---

## 🌐 Step 6: Access the API

Once the server is running, you can access:

- **API Base URL:** `http://127.0.0.1:8000` or `http://localhost:8000`
- **API Documentation (Swagger UI):** `http://127.0.0.1:8000/docs`
- **Alternative API Docs (ReDoc):** `http://127.0.0.1:8000/redoc`
- **Health Check:** `http://127.0.0.1:8000/health`
- **Root Endpoint:** `http://127.0.0.1:8000/`

---

## 📁 Project Structure

```
Innsurance Backend Fast API/
├── main.py                 # FastAPI application entry point
├── database.py             # PostgreSQL database configuration
├── models.py               # SQLAlchemy database models
├── schemas.py              # Pydantic schemas for request/response
├── crud.py                 # Database CRUD operations
├── mongo.py                # MongoDB connection
├── azure_storage.py        # Azure Blob Storage integration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── uploads/                # Local file uploads directory
├── routers/                # API route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management
│   ├── policy.py          # Policy management
│   ├── claims.py          # Claims management
│   ├── products.py        # Products
│   ├── contact.py         # Contact forms
│   ├── quotation.py       # Quotations
│   ├── documents.py       # Document management
│   ├── nominee.py         # Nominee management
│   ├── activities.py      # User activities
│   ├── notifications.py   # Notifications
│   ├── payments.py        # Payment processing
│   ├── public.py          # Public endpoints
│   └── life_insurance.py  # Life insurance specific
└── utils/                  # Utility functions
    ├── auth.py            # Authentication utilities
    └── serializers.py     # Data serialization
```

---

## 🔧 Available API Endpoints

### Public Endpoints (No Authentication)
- `GET /` - Welcome message
- `GET /health` - Health check
- Public routes from `routers/public.py`

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- Routes from `routers/auth.py`

### Protected Endpoints (Require Authentication)
- **Users:** `/users/*` - User management
- **Policies:** `/policies/*` - Policy operations
- **Claims:** `/claims/*` - Claims management
- **Products:** `/products/*` - Product information
- **Documents:** `/documents/*` - Document uploads/downloads
- **Payments:** `/payments/*` - Payment processing
- And more...

See `http://127.0.0.1:8000/docs` for complete API documentation.

---

## 🐛 Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'passlib'`

**Solution:**
```powershell
pip install passlib[bcrypt]
```

### Issue: `AttributeError: module 'bcrypt' has no attribute '__about__'`

**Problem:** Compatibility issue between `passlib` 1.7.4 and `bcrypt` 5.0.0+

**Solution:**
```powershell
# Uninstall incompatible bcrypt version
pip uninstall bcrypt -y

# Install compatible version (bcrypt < 4.0.0)
pip install "bcrypt<4.0.0"
```

**Note:** `requirements.txt` now pins `bcrypt<4.0.0` to prevent this issue.

### Issue: `ModuleNotFoundError: No module named 'xxx'`

**Solution:**
```powershell
# Install all dependencies
pip install -r requirements.txt
```

### Issue: Database Connection Error

**Solution:**
1. Check your `DATABASE_URL` in `.env` file
2. Verify PostgreSQL server is running and accessible
3. Check firewall rules if using Azure PostgreSQL
4. Ensure SSL mode is set correctly (`sslmode=require` for Azure)

### Issue: MongoDB Connection Error

**Solution:**
1. Check your `MONGO_URI` in `.env` file
2. Verify MongoDB Atlas cluster is accessible
3. Check IP whitelist in MongoDB Atlas
4. Verify credentials are correct

### Issue: Port Already in Use

**Solution:**
```powershell
# Use a different port
uvicorn main:app --reload --port 8001
```

### Issue: CORS Errors

**Solution:**
1. Check `CORS_ORIGINS` in `.env` file
2. Ensure your frontend URL is included in the list
3. Default includes: `http://localhost:3000`, `http://localhost:5173`

---

## 📝 Common Commands

### Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Deactivate Virtual Environment
```powershell
deactivate
```

### Install Dependencies
```powershell
pip install -r requirements.txt
```

### Run Server
```powershell
uvicorn main:app --reload
```

### Check Installed Packages
```powershell
pip list
```

### Update Dependencies
```powershell
pip install --upgrade -r requirements.txt
```

---

## 🔐 Security Notes

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use environment variables** for all secrets
3. **Change default passwords** in production
4. **Enable SSL/TLS** for database connections (Azure requires it)
5. **Use strong passwords** for database and MongoDB

---

## 📚 Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **MongoDB Motor Documentation:** https://motor.readthedocs.io/
- **Uvicorn Documentation:** https://www.uvicorn.org/

---

## ✅ Verification Checklist

Before running, ensure:

- [ ] Python 3.9+ is installed
- [ ] Virtual environment is created and activated
- [ ] All dependencies are installed (`pip install -r requirements.txt`)
- [ ] `.env` file is created with correct credentials
- [ ] PostgreSQL database is accessible
- [ ] MongoDB is accessible (if using)
- [ ] Port 8000 is available (or use different port)

---

## 🎯 Quick Start Summary

```powershell
# 1. Navigate to backend directory
cd "D:\Project\insurance_project_demo_27-11-25\insurance-ai-frontend\Innsurance Backend Fast API"

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Install dependencies (if not already installed)
pip install -r requirements.txt

# 4. Create .env file with your credentials (if not exists)

# 5. Run the server
uvicorn main:app --reload
```

**That's it!** Your API should now be running at `http://127.0.0.1:8000`

---

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set correctly
3. Check database connectivity
4. Review server logs for error messages

---

**Last Updated:** Current Session  
**FastAPI Version:** 0.104.1+  
**Python Version:** 3.14

