# 🚀 Quick Start Guide - FastAPI Backend

## One-Command Setup (If venv exists)

```powershell
cd "D:\Project\insurance_project_demo_27-11-25\insurance-ai-frontend\Innsurance Backend Fast API"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

## Full Setup (First Time)

### 1. Activate Virtual Environment
```powershell
cd "D:\Project\insurance_project_demo_27-11-25\insurance-ai-frontend\Innsurance Backend Fast API"
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Create .env File (Optional - uses defaults if not present)
```env
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB=insurance_ai
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 4. Run Server
```powershell
uvicorn main:app --reload
```

## Access Points

- **API:** http://127.0.0.1:8000
- **Docs:** http://127.0.0.1:8000/docs
- **Health:** http://127.0.0.1:8000/health

## Common Issues

| Issue | Solution |
|-------|----------|
| Module not found | `pip install -r requirements.txt` |
| Port in use | `uvicorn main:app --reload --port 8001` |
| Database error | Check `.env` DATABASE_URL |
| MongoDB error | Check `.env` MONGO_URI |

## Dependencies

- FastAPI + Uvicorn
- PostgreSQL (psycopg2)
- MongoDB (motor)
- Azure Storage (optional)
- Password Hashing (passlib)

See `RUN_GUIDE.md` for detailed documentation.

