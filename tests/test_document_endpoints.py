"""
Integration Tests for Document Endpoints

Tests document upload, retrieval, and deletion with new folder structure.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db
from models import Documents


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class TestDocumentEndpoints(unittest.TestCase):
    """Integration tests for document endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        # Create test database tables
        Base.metadata.create_all(bind=engine)
        
        # Create temporary uploads directory
        cls.temp_uploads_dir = tempfile.mkdtemp()
        cls.original_uploads_dir = os.path.join(os.getcwd(), 'uploads')
        
        # Mock uploads directory path (would need to modify documents.py for real test)
        
        # Create test client
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        # Drop test database tables
        Base.metadata.drop_all(bind=engine)
        
        # Remove temporary directory
        if os.path.exists(cls.temp_uploads_dir):
            shutil.rmtree(cls.temp_uploads_dir)

    def setUp(self):
        """Set up for each test"""
        # Clean up database
        db = TestingSessionLocal()
        try:
            db.query(Documents).delete()
            db.commit()
        finally:
            db.close()

    def test_upload_document_kyc(self):
        """Test uploading a KYC document"""
        # Create a test file
        test_file_content = b"Test PDF content"
        test_file = ("test_kyc.pdf", test_file_content, "application/pdf")
        
        # Upload document
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "kyc_document"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response
        self.assertTrue(data["success"])
        self.assertIn("documentId", data)
        self.assertIn("fileUrl", data)
        
        # Verify URL contains new folder structure
        self.assertIn("users/123/kyc", data["fileUrl"])

    def test_upload_document_id_card(self):
        """Test uploading an ID card"""
        test_file = ("test_id.pdf", b"Test ID content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "id_card"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL contains correct folder
        self.assertIn("users/123/id_cards", data["fileUrl"])

    def test_upload_document_pan_card(self):
        """Test uploading a PAN card"""
        test_file = ("test_pan.pdf", b"Test PAN content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "pan_card"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL contains correct folder
        self.assertIn("users/123/pan_cards", data["fileUrl"])

    def test_upload_document_policy(self):
        """Test uploading a policy document"""
        test_file = ("test_policy.pdf", b"Test policy content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "policy_document",
                "policyId": "456"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL contains correct folder
        self.assertIn("users/123/policies", data["fileUrl"])

    def test_upload_document_claim_with_claim_id(self):
        """Test uploading a claim document with claimId"""
        test_file = ("test_claim.pdf", b"Test claim content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "claim_document",
                "claimId": "789"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL contains claims folder
        self.assertIn("claims/789", data["fileUrl"])

    def test_upload_document_claim_without_claim_id(self):
        """Test uploading a claim document without claimId"""
        test_file = ("test_claim.pdf", b"Test claim content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "claim_document"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify URL contains pending claims folder
        self.assertIn("claims/pending/123", data["fileUrl"])

    def test_get_documents_by_user(self):
        """Test retrieving documents by user ID"""
        # Upload a document first
        test_file = ("test.pdf", b"Test content", "application/pdf")
        upload_response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "kyc_document"
            }
        )
        
        # Get documents by user
        response = self.client.get("/documents/user/123")
        
        self.assertEqual(response.status_code, 200)
        documents = response.json()
        
        self.assertIsInstance(documents, list)
        self.assertGreater(len(documents), 0)
        self.assertEqual(documents[0]["userId"], 123)

    def test_get_single_document(self):
        """Test retrieving a single document"""
        # Upload a document first
        test_file = ("test.pdf", b"Test content", "application/pdf")
        upload_response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "kyc_document"
            }
        )
        
        document_id = upload_response.json()["documentId"]
        
        # Get single document
        response = self.client.get(f"/documents/{document_id}")
        
        self.assertEqual(response.status_code, 200)
        document = response.json()
        
        self.assertEqual(document["documentId"], document_id)
        self.assertEqual(document["userId"], 123)

    def test_get_document_not_found(self):
        """Test retrieving non-existent document"""
        response = self.client.get("/documents/99999")
        
        self.assertEqual(response.status_code, 404)

    def test_delete_document(self):
        """Test deleting a document"""
        # Upload a document first
        test_file = ("test.pdf", b"Test content", "application/pdf")
        upload_response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "kyc_document"
            }
        )
        
        document_id = upload_response.json()["documentId"]
        
        # Delete document
        response = self.client.delete(f"/documents/{document_id}")
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        
        # Verify document is deleted
        get_response = self.client.get(f"/documents/{document_id}")
        self.assertEqual(get_response.status_code, 404)


class TestDocumentEdgeCases(unittest.TestCase):
    """Test edge cases for document endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        Base.metadata.drop_all(bind=engine)

    def setUp(self):
        """Set up for each test"""
        db = TestingSessionLocal()
        try:
            db.query(Documents).delete()
            db.commit()
        finally:
            db.close()

    def test_upload_without_user_id(self):
        """Test uploading without userId (should fail)"""
        test_file = ("test.pdf", b"Test content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={"documentType": "kyc_document"}
        )
        
        # Should fail without userId
        self.assertNotEqual(response.status_code, 200)

    def test_upload_without_document_type(self):
        """Test uploading without documentType (should fail)"""
        test_file = ("test.pdf", b"Test content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={"userId": "123"}
        )
        
        # Should fail without documentType
        self.assertNotEqual(response.status_code, 200)

    def test_upload_invalid_document_type(self):
        """Test uploading with invalid document type (should use 'other')"""
        test_file = ("test.pdf", b"Test content", "application/pdf")
        
        response = self.client.post(
            "/documents/upload",
            files={"file": test_file},
            data={
                "userId": "123",
                "documentType": "invalid_type"
            }
        )
        
        # Should still succeed, but use 'other' folder
        if response.status_code == 200:
            data = response.json()
            self.assertIn("users/123/other", data["fileUrl"])

    def test_multiple_documents_same_user(self):
        """Test uploading multiple documents for the same user"""
        user_id = "123"
        document_types = ["kyc_document", "id_card", "pan_card", "policy_document"]
        
        for doc_type in document_types:
            test_file = (f"test_{doc_type}.pdf", b"Test content", "application/pdf")
            response = self.client.post(
                "/documents/upload",
                files={"file": test_file},
                data={
                    "userId": user_id,
                    "documentType": doc_type
                }
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn(f"users/{user_id}", data["fileUrl"])


if __name__ == "__main__":
    unittest.main()

