# Azure Setup Configuration

## ✅ Completed Setup

### 1. Azure PostgreSQL Database
- **Status**: ✅ Configured
- **File**: `database.py`
- **Connection**: Azure PostgreSQL with SSL
- **Host**: `insurance-ai-postgres-dev.postgres.database.azure.com`
- **Database**: `postgres`
- **SSL Mode**: Required

### 2. Azure File Storage
- **Status**: ✅ Configured
- **File**: `azure_storage.py`
- **Account**: `tfstateacct123`
- **Container**: `insurance-documents` (auto-created)
- **Features**: Upload, Download, Delete, List files

### 3. Environment Configuration
- **Status**: ✅ Created
- **File**: `.env.example`
- **Contains**: Database URL, Storage connection string, API config

### 4. Dependencies
- **Status**: ✅ Updated
- **File**: `requirements.txt`
- **Added**: Azure Storage Blob SDK, psycopg2-binary

### 5. API Configuration
- **Status**: ✅ Updated
- **File**: `main.py`
- **Features**: CORS middleware, Health check endpoint

### 6. Document Upload
- **Status**: ✅ Implemented
- **File**: `routers/documents.py`
- **Features**: Azure Storage integration, folder organization

## 🔧 Configuration Steps

### Step 1: Create .env File
```bash
cd "Innsurance Backend Fast API/fastapi_insurance_project_backend"
cp .env.example .env
```

### Step 2: Update .env with Your Credentials
```env
# Azure PostgreSQL
DATABASE_URL=postgresql://dbadmin:admin%40123@insurance-ai-postgres-dev.postgres.database.azure.com:5432/postgres?sslmode=require

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=tfstateacct123;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net
AZURE_STORAGE_ACCOUNT_NAME=tfstateacct123
AZURE_STORAGE_ACCOUNT_KEY=YOUR_ACCOUNT_KEY
AZURE_STORAGE_CONTAINER_NAME=insurance-documents
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Test Connection
```bash
# Start server
uvicorn main:app --reload

# Check health
curl http://localhost:8000/health

# Check Swagger UI
# Open http://localhost:8000/docs
```

## 📝 Important Notes

1. **Password Encoding**: Use URL encoding for special characters (`@` becomes `%40`)
2. **SSL Required**: Azure PostgreSQL requires SSL (`sslmode=require`)
3. **Connection Pooling**: Configured for Azure with connection recycling
4. **Storage Container**: Will be created automatically if it doesn't exist
5. **File Organization**: Files are organized by folder (policies, claims, kyc, documents)

## 🧪 Testing

### Test Database Connection
```python
from database import engine
from sqlalchemy import text

# Test connection
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("Database connected:", result.scalar())
```

### Test Azure Storage
```python
from azure_storage import azure_storage

# Test upload
test_content = b"Test file content"
url = azure_storage.upload_file(test_content, "test.txt", "test")
print("File uploaded:", url)
```

## 🔒 Security

- Never commit `.env` file to git
- Use environment variables for sensitive data
- Rotate Azure Storage keys regularly
- Use Azure Key Vault for production

## 📚 Next Steps

1. Update database schema (add userId to Policy, etc.)
2. Enhance CRUD operations
3. Update API routers
4. Integrate frontend
5. Test file uploads
6. Test database operations

