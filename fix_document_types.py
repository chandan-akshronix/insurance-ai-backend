"""
Migration script to fix documentType values in existing database records.

This script extracts the documentType from the documentUrl folder path and updates
the database records with the correct documentType value.

Usage:
    python fix_document_types.py --dry-run    # Test without making changes
    python fix_document_types.py --live       # Apply changes to database
    python fix_document_types.py --user-id 6  # Fix documents for specific user only
"""

import argparse
import logging
import os
import sys
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
from models import Documents
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_document_types.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Reverse mapping from folder name to documentType
# This is the inverse of FOLDER_MAP in documents.py
FOLDER_TO_DOCUMENT_TYPE: Dict[str, str] = {
    "kyc": "kyc_document",
    "id_cards": "id_card",
    "pan_cards": "pan_card",
    "policies": "policy_document",
    "claims": "claim_document",
    "other": "other"
}

# Allowed document types (for validation)
ALLOWED_DOCUMENT_TYPES = {
    "kyc_document",
    "id_card",
    "pan_card",
    "policy_document",
    "claim_document",
    "other"
}


def extract_folder_from_url(document_url: str) -> Optional[str]:
    """
    Extract folder path from document URL.
    
    Handles both Azure Blob Storage URLs and local storage URLs.
    
    Examples:
        Azure: https://account.blob.core.windows.net/container/users/6/id_cards/file.pdf
        Local: http://localhost:8000/uploads/users/6/id_cards/file.pdf
    
    Returns:
        Folder path (e.g., "users/6/id_cards") or None if extraction fails
    """
    if not document_url:
        return None
    
    try:
        # Parse URL
        parsed = urlparse(document_url)
        path = parsed.path
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Handle Azure Blob Storage URLs
        # Format: /container/users/{userId}/{folder}/file
        if 'blob.core.windows.net' in document_url:
            # Extract path after container name
            parts = path.split('/')
            if len(parts) >= 4 and parts[1] in ['users', 'claims']:
                # Reconstruct folder path: users/{userId}/{folder}
                if parts[1] == 'users' and len(parts) >= 4:
                    return '/'.join(parts[1:4])  # users/{userId}/{folder}
                elif parts[1] == 'claims':
                    if len(parts) >= 3:
                        return '/'.join(parts[1:3])  # claims/{claimId}
                    elif len(parts) >= 4:
                        return '/'.join(parts[1:4])  # claims/pending/{userId}
        
        # Handle local storage URLs
        # Format: /uploads/users/{userId}/{folder}/file
        if '/uploads/' in document_url:
            parts = path.split('/')
            uploads_idx = None
            for i, part in enumerate(parts):
                if part == 'uploads':
                    uploads_idx = i
                    break
            
            if uploads_idx is not None and len(parts) > uploads_idx + 3:
                # Extract folder path after /uploads/
                folder_parts = parts[uploads_idx + 1:]  # Skip 'uploads'
                if len(folder_parts) >= 3:
                    return '/'.join(folder_parts[:3])  # users/{userId}/{folder}
                elif len(folder_parts) >= 2 and folder_parts[0] == 'claims':
                    return '/'.join(folder_parts[:2])  # claims/{claimId}
        
        # Fallback: try to extract from any path
        parts = path.split('/')
        if len(parts) >= 3:
            if parts[0] == 'users' or parts[0] == 'claims':
                return '/'.join(parts[:min(3, len(parts))])
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting folder from URL '{document_url}': {e}")
        return None


def derive_document_type_from_folder(folder_path: str) -> Optional[str]:
    """
    Derive documentType from folder path.
    
    Examples:
        "users/6/id_cards" -> "id_card"
        "users/6/pan_cards" -> "pan_card"
        "users/6/policies" -> "policy_document"
        "users/6/kyc" -> "kyc_document"
        "users/6/other" -> "other"
        "claims/123" -> "claim_document"
    
    Returns:
        documentType string or None if cannot be determined
    """
    if not folder_path:
        return None
    
    # Split folder path
    parts = folder_path.split('/')
    
    # Handle claims documents
    if len(parts) >= 1 and parts[0] == 'claims':
        return "claim_document"
    
    # Handle user documents: users/{userId}/{folder}
    if len(parts) >= 3 and parts[0] == 'users':
        folder_name = parts[2]  # Get folder name (id_cards, pan_cards, etc.)
        return FOLDER_TO_DOCUMENT_TYPE.get(folder_name, "other")
    
    # Handle legacy paths (if any)
    if len(parts) >= 1:
        folder_name = parts[-1]  # Get last part
        if folder_name in FOLDER_TO_DOCUMENT_TYPE:
            return FOLDER_TO_DOCUMENT_TYPE[folder_name]
    
    return None


def get_document_type_from_url(document_url: str) -> Optional[str]:
    """
    Get documentType from document URL.
    
    This is the main function that extracts documentType from URL.
    
    Returns:
        documentType string or None if cannot be determined
    """
    folder_path = extract_folder_from_url(document_url)
    if not folder_path:
        return None
    
    return derive_document_type_from_folder(folder_path)


def update_document_type(db: Session, document: Documents, new_document_type: str, dry_run: bool = False) -> bool:
    """
    Update documentType for a document record.
    
    Args:
        db: Database session
        document: Document record to update
        new_document_type: New documentType value
        dry_run: If True, only log the change without applying it
    
    Returns:
        True if update was successful (or would be in dry-run), False otherwise
    """
    try:
        old_type = document.documentType
        document_id = document.id
        user_id = document.userId
        url = document.documentUrl
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update document {document_id} (userId: {user_id}): '{old_type}' -> '{new_document_type}' | URL: {url}")
            return True
        else:
            document.documentType = new_document_type
            db.commit()
            logger.info(f"Updated document {document_id} (userId: {user_id}): '{old_type}' -> '{new_document_type}' | URL: {url}")
            return True
    
    except Exception as e:
        logger.error(f"Error updating document {document.id}: {e}")
        db.rollback()
        return False


def fix_document_types(user_id: Optional[int] = None, dry_run: bool = True):
    """
    Main function to fix documentType values in database.
    
    Args:
        user_id: Optional user ID to filter documents (if None, processes all)
        dry_run: If True, only shows what would be changed without applying
    """
    db = SessionLocal()
    
    try:
        # Get all documents or documents for specific user
        if user_id:
            logger.info(f"Fetching documents for user {user_id}...")
            documents = db.query(Documents).filter(Documents.userId == user_id).all()
        else:
            logger.info("Fetching all documents...")
            documents = db.query(Documents).all()
        
        total_count = len(documents)
        logger.info(f"Found {total_count} document(s) to process")
        
        if total_count == 0:
            logger.info("No documents found. Exiting.")
            return
        
        # Statistics
        stats = {
            'total': total_count,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'no_url': 0,
            'cannot_determine': 0,
            'already_correct': 0
        }
        
        # Process each document
        for doc in documents:
            try:
                # Check if document has URL
                if not doc.documentUrl:
                    logger.warning(f"Document {doc.id} has no URL. Skipping.")
                    stats['no_url'] += 1
                    stats['skipped'] += 1
                    continue
                
                # Get current documentType
                current_type = doc.documentType or ""
                
                # Extract documentType from URL
                new_type = get_document_type_from_url(doc.documentUrl)
                
                if not new_type:
                    logger.warning(f"Document {doc.id}: Cannot determine documentType from URL '{doc.documentUrl}'. Skipping.")
                    stats['cannot_determine'] += 1
                    stats['skipped'] += 1
                    continue
                
                # Check if update is needed
                if current_type == new_type:
                    logger.debug(f"Document {doc.id}: documentType already correct ('{current_type}'). Skipping.")
                    stats['already_correct'] += 1
                    stats['skipped'] += 1
                    continue
                
                # Update documentType
                if update_document_type(db, doc, new_type, dry_run):
                    stats['updated'] += 1
                else:
                    stats['errors'] += 1
                    stats['skipped'] += 1
            
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {e}")
                stats['errors'] += 1
                stats['skipped'] += 1
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total documents: {stats['total']}")
        logger.info(f"Updated: {stats['updated']}")
        logger.info(f"Already correct: {stats['already_correct']}")
        logger.info(f"Skipped: {stats['skipped']} (no URL: {stats['no_url']}, cannot determine: {stats['cannot_determine']})")
        logger.info(f"Errors: {stats['errors']}")
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes were made to the database.")
            logger.info("Run with --live flag to apply changes.")
        else:
            logger.info("\n✅ Changes have been applied to the database.")
        
        logger.info("="*60)
    
    except Exception as e:
        logger.error(f"Fatal error during migration: {e}", exc_info=True)
        db.rollback()
        raise
    
    finally:
        db.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Fix documentType values in existing database records based on URL folder paths.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (test without making changes)
  python fix_document_types.py --dry-run
  
  # Fix documents for specific user only (dry-run)
  python fix_document_types.py --dry-run --user-id 6
  
  # Apply changes to all documents
  python fix_document_types.py --live
  
  # Apply changes for specific user only
  python fix_document_types.py --live --user-id 6
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - show what would be changed without applying changes'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Live mode - actually update the database'
    )
    
    parser.add_argument(
        '--user-id',
        type=int,
        default=None,
        help='Only process documents for specific user ID'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.dry_run and not args.live:
        logger.error("Error: You must specify either --dry-run or --live")
        parser.print_help()
        sys.exit(1)
    
    if args.dry_run and args.live:
        logger.error("Error: Cannot specify both --dry-run and --live")
        parser.print_help()
        sys.exit(1)
    
    dry_run = args.dry_run
    user_id = args.user_id
    
    # Run migration
    logger.info("="*60)
    logger.info("DOCUMENT TYPE MIGRATION SCRIPT")
    logger.info("="*60)
    logger.info(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will update database)'}")
    if user_id:
        logger.info(f"User ID filter: {user_id}")
    logger.info("="*60 + "\n")
    
    try:
        fix_document_types(user_id=user_id, dry_run=dry_run)
        logger.info("\n✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

