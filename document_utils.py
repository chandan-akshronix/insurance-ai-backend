"""
Document Utility Functions

Helper functions for document folder path derivation and management.
These functions can be used by migration scripts and queries.
"""
from typing import Optional
import re

# Folder mapping for document types
FOLDER_MAP = {
    "kyc_document": "kyc",
    "id_card": "id_cards",
    "pan_card": "pan_cards",
    "policy_document": "policies",
    "claim_document": "claims",
    "other": "other"
}


def derive_folder_path(userId: int, documentType: str, claimId: Optional[int] = None, category: Optional[str] = None) -> str:
    """
    Derive the folder path for a document based on user ID, document type, optional claim ID, and category.
    
    This function implements the same logic as the upload function to determine folder structure.
    Useful for migration scripts, queries, and document management.
    
    Args:
        userId: User ID
        documentType: Type of document (kyc_document, id_card, pan_card, policy_document, claim_document, other)
        claimId: Optional claim ID (used for claim_document type)
        category: Optional category/name for claim documents (e.g., "death-certificate", "claim-form")
    
    Returns:
        Folder path string (e.g., "users/123/kyc", "claims/456/death-certificate", "claims/pending/123/claim-form")
    
    Examples:
        >>> derive_folder_path(123, "kyc_document")
        "users/123/kyc"
        >>> derive_folder_path(123, "id_card")
        "users/123/id_cards"
        >>> derive_folder_path(123, "pan_card")
        "users/123/pan_cards"
        >>> derive_folder_path(123, "policy_document")
        "users/123/policies"
        >>> derive_folder_path(123, "claim_document", claimId=456, category="death-certificate")
        "claims/456/death-certificate"
        >>> derive_folder_path(123, "claim_document", claimId=456)
        "claims/456"
        >>> derive_folder_path(123, "claim_document", category="claim-form")
        "claims/pending/123/claim-form"
        >>> derive_folder_path(123, "claim_document")
        "claims/pending/123"
        >>> derive_folder_path(123, "other")
        "users/123/other"
    """
    base_folder = FOLDER_MAP.get(documentType, "other")
    
    # Handle claims documents separately with category subfolders
    if documentType == "claim_document":
        if claimId:
            # For claim documents with claimId: claims/{claimId}/{category}/
            if category:
                # Normalize category for folder name using helper function
                normalized_category = normalize_category_for_folder(category)
                return f"claims/{claimId}/{normalized_category}"
            else:
                # Fallback to old structure if no category provided (backward compatibility)
                return f"claims/{claimId}"
        else:
            # For pending claims: claims/pending/{userId}/{category}/
            if category:
                normalized_category = normalize_category_for_folder(category)
                return f"claims/pending/{userId}/{normalized_category}"
            else:
                # Fallback to old structure if no category provided (backward compatibility)
                return f"claims/pending/{userId}"
    else:
        # User documents organized by userId and document type
        return f"users/{userId}/{base_folder}"


def extract_folder_from_url(url: str, container_name: str = "insurance-documents") -> Optional[str]:
    """
    Extract folder path from a document URL.
    
    This can be used to determine the folder path of existing documents
    from their stored URLs (useful for migration).
    
    Args:
        url: Document URL (either Azure Blob Storage URL or local storage URL)
        container_name: Optional container name to handle (ignores it logic-wise but accepts argument)
    
    Returns:
        Folder path string if found, None otherwise
    
    Examples:
        >>> extract_folder_from_url("http://localhost:8000/uploads/users/123/kyc/uuid.pdf")
        "users/123/kyc"
        >>> extract_folder_from_url("https://account.blob.core.windows.net/insurance-documents/users/123/kyc/uuid.pdf")
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


def normalize_category_for_folder(category: str) -> str:
    """
    Normalize category name for use in folder paths.
    
    Converts category names to folder-safe format:
    - Lowercase
    - Replace spaces and underscores with hyphens
    - Remove special characters except hyphens and alphanumeric
    
    Args:
        category: Category name (e.g., "Death Certificate", "FIR Copy (if accidental)")
    
    Returns:
        Normalized category name (e.g., "death-certificate", "fir-copy-if-accidental")
    
    Examples:
        >>> normalize_category_for_folder("Death Certificate")
        "death-certificate"
        >>> normalize_category_for_folder("FIR Copy (if accidental)")
        "fir-copy-if-accidental"
        >>> normalize_category_for_folder("Claim Form")
        "claim-form"
    """
    # Convert to lowercase
    normalized = category.lower()
    # Replace spaces and underscores with hyphens
    normalized = normalized.replace(' ', '-').replace('_', '-')
    # Remove any special characters except hyphens and alphanumeric
    normalized = re.sub(r'[^a-z0-9\-]', '', normalized)
    # Remove multiple consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized


def has_category_folder(url: str) -> bool:
    """
    Check if document URL indicates category-based folder structure.
    
    This helps identify if a document uses the new category-based structure
    or the old structure (for backward compatibility).
    
    Args:
        url: Document URL (Azure Blob Storage or local storage)
    
    Returns:
        True if URL indicates category-based folder structure, False otherwise
    
    Examples:
        >>> has_category_folder("https://account.blob.core.windows.net/container/claims/123/death-certificate/file.pdf")
        True
        >>> has_category_folder("https://account.blob.core.windows.net/container/claims/123/file.pdf")
        False
    """
    folder_path = extract_folder_from_url(url)
    if not folder_path:
        return False
    
    # Check if folder path has category structure: claims/{claimId}/{category}
    # or claims/pending/{userId}/{category}
    parts = folder_path.split('/')
    if len(parts) >= 3 and parts[0] == 'claims':
        # New structure: claims/{claimId}/{category} or claims/pending/{userId}/{category}
        if parts[1] == 'pending':
            return len(parts) >= 4  # claims/pending/{userId}/{category}
        else:
            return len(parts) >= 3  # claims/{claimId}/{category}
    
    return False


def get_document_type_folder(documentType: str) -> str:
    """
    Get the base folder name for a document type.
    
    Args:
        documentType: Type of document
    
    Returns:
        Base folder name (e.g., "kyc", "id_cards", "policies")
    """
    return FOLDER_MAP.get(documentType, "other")

