"""
Document Utility Functions

Helper functions for document folder path derivation and management.
These functions can be used by migration scripts and queries.
"""
from typing import Optional

# Folder mapping for document types
FOLDER_MAP = {
    "kyc_document": "kyc",
    "id_card": "id_cards",
    "pan_card": "pan_cards",
    "policy_document": "policies",
    "claim_document": "claims",
    "other": "other"
}


def derive_folder_path(userId: int, documentType: str, claimId: Optional[int] = None) -> str:
    """
    Derive the folder path for a document based on user ID, document type, and optional claim ID.
    
    This function implements the same logic as the upload function to determine folder structure.
    Useful for migration scripts, queries, and document management.
    
    Args:
        userId: User ID
        documentType: Type of document (kyc_document, id_card, pan_card, policy_document, claim_document, other)
        claimId: Optional claim ID (used for claim_document type)
    
    Returns:
        Folder path string (e.g., "users/123/kyc", "claims/456", "claims/pending/123")
    
    Examples:
        >>> derive_folder_path(123, "kyc_document")
        "users/123/kyc"
        >>> derive_folder_path(123, "id_card")
        "users/123/id_cards"
        >>> derive_folder_path(123, "pan_card")
        "users/123/pan_cards"
        >>> derive_folder_path(123, "policy_document")
        "users/123/policies"
        >>> derive_folder_path(123, "claim_document", claimId=456)
        "claims/456"
        >>> derive_folder_path(123, "claim_document")
        "claims/pending/123"
        >>> derive_folder_path(123, "other")
        "users/123/other"
    """
    base_folder = FOLDER_MAP.get(documentType, "other")
    
    # Handle claims documents separately
    if documentType == "claim_document" and claimId:
        return f"claims/{claimId}"
    elif documentType == "claim_document" and not claimId:
        return f"claims/pending/{userId}"
    else:
        # User documents organized by userId and document type
        return f"users/{userId}/{base_folder}"


def extract_folder_from_url(url: str) -> Optional[str]:
    """
    Extract folder path from a document URL.
    
    This can be used to determine the folder path of existing documents
    from their stored URLs (useful for migration).
    
    Args:
        url: Document URL (either Azure Blob Storage URL or local storage URL)
    
    Returns:
        Folder path string if found, None otherwise
    
    Examples:
        >>> extract_folder_from_url("http://localhost:8000/uploads/users/123/kyc/uuid.pdf")
        "users/123/kyc"
        >>> extract_folder_from_url("https://account.blob.core.windows.net/container/users/123/kyc/uuid.pdf")
        "users/123/kyc"
    """
    try:
        # Handle local storage URLs
        if '/uploads/' in url:
            parts = url.split('/uploads/')
            if len(parts) > 1:
                path = parts[1]
                # Remove filename (last part after /)
                folder_path = '/'.join(path.split('/')[:-1])
                return folder_path if folder_path else None
        
        # Handle Azure Blob Storage URLs
        elif 'blob.core.windows.net' in url:
            # Extract path after container name
            # Format: https://account.blob.core.windows.net/container/folder/file.pdf
            parts = url.split('blob.core.windows.net/')
            if len(parts) > 1:
                path = parts[1]
                # Remove container name and filename
                path_parts = path.split('/')
                if len(path_parts) > 2:
                    # Skip container name (first part) and filename (last part)
                    folder_path = '/'.join(path_parts[1:-1])
                    return folder_path if folder_path else None
        
    except Exception as e:
        print(f"Error extracting folder from URL: {e}")
        return None
    
    return None


def get_document_type_folder(documentType: str) -> str:
    """
    Get the base folder name for a document type.
    
    Args:
        documentType: Type of document
    
    Returns:
        Base folder name (e.g., "kyc", "id_cards", "policies")
    """
    return FOLDER_MAP.get(documentType, "other")

