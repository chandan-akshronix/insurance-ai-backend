"""
Unit Tests for Document Utility Functions

Tests folder path generation logic and document utilities.
"""

import unittest
from document_utils import (
    derive_folder_path,
    extract_folder_from_url,
    get_document_type_folder,
    FOLDER_MAP
)


class TestDocumentUtils(unittest.TestCase):
    """Test cases for document utility functions"""

    def test_derive_folder_path_kyc_document(self):
        """Test folder path generation for KYC documents"""
        result = derive_folder_path(userId=123, documentType="kyc_document")
        self.assertEqual(result, "users/123/kyc")

    def test_derive_folder_path_id_card(self):
        """Test folder path generation for ID cards"""
        result = derive_folder_path(userId=123, documentType="id_card")
        self.assertEqual(result, "users/123/id_cards")

    def test_derive_folder_path_pan_card(self):
        """Test folder path generation for PAN cards"""
        result = derive_folder_path(userId=123, documentType="pan_card")
        self.assertEqual(result, "users/123/pan_cards")

    def test_derive_folder_path_policy_document(self):
        """Test folder path generation for policy documents"""
        result = derive_folder_path(userId=123, documentType="policy_document")
        self.assertEqual(result, "users/123/policies")

    def test_derive_folder_path_other(self):
        """Test folder path generation for other documents"""
        result = derive_folder_path(userId=123, documentType="other")
        self.assertEqual(result, "users/123/other")

    def test_derive_folder_path_claim_document_with_claim_id(self):
        """Test folder path generation for claim documents with claimId"""
        result = derive_folder_path(userId=123, documentType="claim_document", claimId=456)
        self.assertEqual(result, "claims/456")

    def test_derive_folder_path_claim_document_without_claim_id(self):
        """Test folder path generation for claim documents without claimId"""
        result = derive_folder_path(userId=123, documentType="claim_document")
        self.assertEqual(result, "claims/pending/123")

    def test_derive_folder_path_invalid_document_type(self):
        """Test folder path generation for invalid document type (should default to other)"""
        result = derive_folder_path(userId=123, documentType="invalid_type")
        self.assertEqual(result, "users/123/other")

    def test_derive_folder_path_different_user_ids(self):
        """Test folder path generation with different user IDs"""
        result1 = derive_folder_path(userId=123, documentType="kyc_document")
        result2 = derive_folder_path(userId=456, documentType="kyc_document")
        
        self.assertEqual(result1, "users/123/kyc")
        self.assertEqual(result2, "users/456/kyc")
        self.assertNotEqual(result1, result2)

    def test_extract_folder_from_url_local_storage(self):
        """Test folder extraction from local storage URL"""
        url = "http://localhost:8000/uploads/users/123/kyc/uuid-123.pdf"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "users/123/kyc")

    def test_extract_folder_from_url_local_storage_nested(self):
        """Test folder extraction from nested local storage URL"""
        url = "http://localhost:8000/uploads/claims/456/uuid-123.pdf"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "claims/456")

    def test_extract_folder_from_url_azure_storage(self):
        """Test folder extraction from Azure Blob Storage URL"""
        url = "https://account.blob.core.windows.net/insurance-documents/users/123/kyc/uuid-123.pdf"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "users/123/kyc")

    def test_extract_folder_from_url_azure_claims(self):
        """Test folder extraction from Azure claims URL"""
        url = "https://account.blob.core.windows.net/insurance-documents/claims/456/uuid-123.pdf"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "claims/456")

    def test_extract_folder_from_url_invalid(self):
        """Test folder extraction from invalid URL"""
        url = "invalid-url"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertIsNone(result)

    def test_get_document_type_folder_kyc(self):
        """Test getting folder name for KYC document type"""
        result = get_document_type_folder("kyc_document")
        self.assertEqual(result, "kyc")

    def test_get_document_type_folder_id_card(self):
        """Test getting folder name for ID card document type"""
        result = get_document_type_folder("id_card")
        self.assertEqual(result, "id_cards")

    def test_get_document_type_folder_pan_card(self):
        """Test getting folder name for PAN card document type"""
        result = get_document_type_folder("pan_card")
        self.assertEqual(result, "pan_cards")

    def test_get_document_type_folder_policy(self):
        """Test getting folder name for policy document type"""
        result = get_document_type_folder("policy_document")
        self.assertEqual(result, "policies")

    def test_get_document_type_folder_claims(self):
        """Test getting folder name for claim document type"""
        result = get_document_type_folder("claim_document")
        self.assertEqual(result, "claims")

    def test_get_document_type_folder_other(self):
        """Test getting folder name for other document type"""
        result = get_document_type_folder("other")
        self.assertEqual(result, "other")

    def test_get_document_type_folder_invalid(self):
        """Test getting folder name for invalid document type (should default to other)"""
        result = get_document_type_folder("invalid_type")
        self.assertEqual(result, "other")

    def test_folder_map_completeness(self):
        """Test that FOLDER_MAP contains all expected document types"""
        expected_types = [
            "kyc_document",
            "id_card",
            "pan_card",
            "policy_document",
            "claim_document",
            "other"
        ]
        
        for doc_type in expected_types:
            self.assertIn(doc_type, FOLDER_MAP)

    def test_folder_path_consistency(self):
        """Test consistency between derive_folder_path and folder map"""
        test_cases = [
            ("kyc_document", 123, None, "users/123/kyc"),
            ("id_card", 123, None, "users/123/id_cards"),
            ("pan_card", 123, None, "users/123/pan_cards"),
            ("policy_document", 123, None, "users/123/policies"),
            ("claim_document", 123, 456, "claims/456"),
            ("claim_document", 123, None, "claims/pending/123"),
            ("other", 123, None, "users/123/other"),
        ]
        
        for doc_type, user_id, claim_id, expected_path in test_cases:
            result = derive_folder_path(userId=user_id, documentType=doc_type, claimId=claim_id)
            self.assertEqual(result, expected_path, 
                           f"Failed for {doc_type}, userId={user_id}, claimId={claim_id}")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases for document utilities"""

    def test_user_id_zero(self):
        """Test with userId = 0 (edge case)"""
        result = derive_folder_path(userId=0, documentType="kyc_document")
        self.assertEqual(result, "users/0/kyc")

    def test_user_id_large_number(self):
        """Test with very large userId"""
        result = derive_folder_path(userId=999999, documentType="kyc_document")
        self.assertEqual(result, "users/999999/kyc")

    def test_claim_id_zero(self):
        """Test with claimId = 0"""
        result = derive_folder_path(userId=123, documentType="claim_document", claimId=0)
        self.assertEqual(result, "claims/0")

    def test_empty_document_type(self):
        """Test with empty document type (should default to other)"""
        result = derive_folder_path(userId=123, documentType="")
        self.assertEqual(result, "users/123/other")

    def test_url_with_query_parameters(self):
        """Test folder extraction from URL with query parameters"""
        url = "http://localhost:8000/uploads/users/123/kyc/uuid-123.pdf?token=abc123"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "users/123/kyc")

    def test_url_with_fragment(self):
        """Test folder extraction from URL with fragment"""
        url = "http://localhost:8000/uploads/users/123/kyc/uuid-123.pdf#section1"
        result = extract_folder_from_url(url, "insurance-documents")
        self.assertEqual(result, "users/123/kyc")


if __name__ == "__main__":
    unittest.main()

