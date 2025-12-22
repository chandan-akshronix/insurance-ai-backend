"""
Document Migration Script

This script migrates existing documents from the old folder structure to the new nested folder structure:
- Old: kyc/{uuid}.pdf, policies/{uuid}.pdf, etc.
- New: users/{userId}/kyc/{uuid}.pdf, users/{userId}/policies/{uuid}.pdf, etc.

Features:
- Dry-run mode (preview changes without applying)
- Rollback mechanism
- Comprehensive logging
- Edge case handling
- Progress tracking
- Backup creation
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from document_utils import derive_folder_path, extract_folder_from_url
from azure_storage import azure_storage
from database import SessionLocal, engine
from models import Documents
from crud import get_all

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Migration statistics
class MigrationStats:
    def __init__(self):
        self.total_documents = 0
        self.migrated = 0
        self.skipped = 0
        self.failed = 0
        self.already_in_new_structure = 0
        self.errors: List[Dict] = []
    
    def print_summary(self):
        logger.info("=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total documents processed: {self.total_documents}")
        logger.info(f"Successfully migrated: {self.migrated}")
        logger.info(f"Skipped (already in new structure): {self.already_in_new_structure}")
        logger.info(f"Skipped (issues): {self.skipped}")
        logger.info(f"Failed: {self.failed}")
        logger.info("=" * 60)
        
        if self.errors:
            logger.warning(f"\nErrors encountered ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.warning(f"  - Document ID {error.get('document_id')}: {error.get('error')}")
            if len(self.errors) > 10:
                logger.warning(f"  ... and {len(self.errors) - 10} more errors (check log file)")

def is_already_migrated(url: str) -> bool:
    """
    Check if a document is already in the new folder structure.
    New structure indicators:
    - Contains 'users/{userId}/' pattern
    - Contains 'claims/{claimId}/' pattern
    """
    if not url:
        return False
    
    # Check for new structure patterns
    if '/users/' in url or '/claims/' in url:
        # Extract folder path
        old_folder = extract_folder_from_url(url)
        if old_folder:
            # Check if it starts with users/ or claims/
            if old_folder.startswith('users/') or old_folder.startswith('claims/'):
                return True
    
    return False

def get_filename_from_url(url: str) -> Optional[str]:
    """
    Extract filename from document URL.
    """
    if not url:
        return None
    
    try:
        # Get the last part of the URL path
        filename = url.split('/')[-1]
        # Remove query parameters if any
        filename = filename.split('?')[0]
        return filename if filename else None
    except Exception:
        return None

def move_local_file(old_path: str, new_path: str, dry_run: bool = False) -> bool:
    """
    Move a file in local storage from old path to new path.
    
    Args:
        old_path: Full path to old file location
        new_path: Full path to new file location
    
    Returns:
        True if successful, False otherwise
    """
    try:
        old_file = Path(old_path)
        new_file = Path(new_path)
        
        # Check if old file exists
        if not old_file.exists():
            logger.warning(f"Old file does not exist: {old_path}")
            return False
        
        if dry_run:
            logger.info(f"[DRY RUN] Would move: {old_path} -> {new_path}")
            return True
        
        # Create parent directories if needed
        new_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(old_file), str(new_file))
        logger.info(f"Moved file: {old_path} -> {new_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error moving file {old_path} to {new_path}: {e}")
        return False

def copy_azure_blob(old_blob_name: str, new_blob_name: str, dry_run: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Copy a blob in Azure Storage from old location to new location.
    
    Args:
        old_blob_name: Old blob path (e.g., "kyc/uuid.pdf")
        new_blob_name: New blob path (e.g., "users/123/kyc/uuid.pdf")
    
    Returns:
        Tuple of (success: bool, new_url: Optional[str])
    """
    try:
        if not getattr(azure_storage, 'blob_service_client', None):
            logger.error("Azure Storage is not configured")
            return False, None
        
        if dry_run:
            logger.info(f"[DRY RUN] Would copy Azure blob: {old_blob_name} -> {new_blob_name}")
            # Return a mock URL for dry run
            container_name = getattr(azure_storage, 'container_name', 'insurance-documents')
            account_name = getattr(azure_storage, 'account_name', 'account')
            mock_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{new_blob_name}"
            return True, mock_url
        
        # Download from old location
        file_content = azure_storage.download_file(old_blob_name)
        
        # Upload to new location
        # Extract filename and folder from new blob name
        filename = new_blob_name.split('/')[-1]
        new_folder = '/'.join(new_blob_name.split('/')[:-1]) if '/' in new_blob_name else None
        
        new_url = azure_storage.upload_file(file_content, filename, new_folder)
        
        # Delete old blob (optional - uncomment if you want to delete old files after verification)
        # azure_storage.delete_file(old_blob_name)
        
        logger.info(f"Copied Azure blob: {old_blob_name} -> {new_blob_name}")
        return True, new_url
        
    except Exception as e:
        logger.error(f"Error copying Azure blob {old_blob_name} to {new_blob_name}: {e}")
        return False, None

def migrate_document(
    document: Documents,
    db: Session,
    stats: MigrationStats,
    dry_run: bool = False,
    backup_dir: Optional[str] = None
) -> bool:
    """
    Migrate a single document to the new folder structure.
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        doc_id = document.id
        old_url = document.documentUrl
        
        # Skip if already in new structure
        if is_already_migrated(old_url):
            logger.info(f"Document {doc_id} already in new structure, skipping")
            stats.already_in_new_structure += 1
            return True
        
        # Validate required fields
        if not document.userId:
            logger.warning(f"Document {doc_id} has no userId, skipping")
            stats.skipped += 1
            stats.errors.append({
                'document_id': doc_id,
                'error': 'Missing userId'
            })
            return False
        
        if not document.documentType:
            logger.warning(f"Document {doc_id} has no documentType, skipping")
            stats.skipped += 1
            stats.errors.append({
                'document_id': doc_id,
                'error': 'Missing documentType'
            })
            return False
        
        # Determine new folder path
        claim_id = None  # TODO: Extract claimId from document if available
        new_folder = derive_folder_path(document.userId, document.documentType, claim_id)
        
        # Get filename
        filename = get_filename_from_url(old_url)
        if not filename:
            logger.warning(f"Document {doc_id}: Could not extract filename from URL: {old_url}")
            stats.skipped += 1
            stats.errors.append({
                'document_id': doc_id,
                'error': 'Could not extract filename from URL'
            })
            return False
        
        # Determine if Azure or local storage
        is_azure = 'blob.core.windows.net' in old_url if old_url else False
        
        # Handle Azure Blob Storage migration
        if is_azure:
            # Extract old blob name from URL
            container_name = getattr(azure_storage, 'container_name', 'insurance-documents')
            if f'/{container_name}/' in old_url:
                old_blob_name = old_url.split(f'/{container_name}/')[-1]
            else:
                old_blob_name = '/'.join(old_url.split('/')[4:])
            
            new_blob_name = f"{new_folder}/{filename}"
            
            # Skip if already in correct location
            if old_blob_name == new_blob_name:
                logger.info(f"Document {doc_id} already in correct location")
                stats.already_in_new_structure += 1
                return True
            
            # Copy blob to new location
            success, new_url = copy_azure_blob(old_blob_name, new_blob_name, dry_run)
            if success and new_url:
                # Update database URL
                if not dry_run:
                    document.documentUrl = new_url
                    db.commit()
                    logger.info(f"Updated database URL for document {doc_id}")
                elif dry_run:
                    logger.info(f"[DRY RUN] Would update URL to: {new_url}")
                
                stats.migrated += 1
                return True
            else:
                stats.failed += 1
                return False
        
        # Handle local storage migration
        else:
            # Extract old file path
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            if '/uploads/' in old_url:
                old_relative_path = old_url.split('/uploads/')[-1]
                old_file_path = os.path.join(uploads_dir, old_relative_path)
            else:
                logger.warning(f"Document {doc_id}: Invalid local URL format: {old_url}")
                stats.skipped += 1
                return False
            
            new_file_path = os.path.join(uploads_dir, new_folder, filename)
            
            # Skip if already in correct location
            if old_file_path == new_file_path:
                logger.info(f"Document {doc_id} already in correct location")
                stats.already_in_new_structure += 1
                return True
            
            # Create backup if requested
            if backup_dir and not dry_run:
                backup_path = os.path.join(backup_dir, old_relative_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(old_file_path, backup_path)
            
            # Move file to new location
            if move_local_file(old_file_path, new_file_path, dry_run):
                # Update database URL
                if not dry_run:
                    # Construct new URL (assuming base URL)
                    base_url = os.getenv('BASE_URL', 'http://localhost:8000')
                    new_url = f"{base_url.rstrip('/')}/uploads/{new_folder}/{filename}"
                    document.documentUrl = new_url
                    db.commit()
                    logger.info(f"Updated database URL for document {doc_id}")
                
                stats.migrated += 1
                return True
            else:
                stats.failed += 1
                return False
                
    except Exception as e:
        logger.error(f"Error migrating document {document.id}: {e}", exc_info=True)
        stats.failed += 1
        stats.errors.append({
            'document_id': document.id,
            'error': str(e)
        })
        return False

def create_backup_directory() -> str:
    """
    Create a backup directory with timestamp.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.getcwd(), 'migration_backup', timestamp)
    os.makedirs(backup_dir, exist_ok=True)
    logger.info(f"Backup directory created: {backup_dir}")
    return backup_dir

def main(dry_run: bool = True, create_backup: bool = True):
    """
    Main migration function.
    
    Args:
        dry_run: If True, preview changes without applying
        create_backup: If True, create backup of files before migration
    """
    logger.info("=" * 60)
    logger.info("DOCUMENT MIGRATION SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE MIGRATION'}")
    logger.info(f"Backup: {'Yes' if create_backup else 'No'}")
    logger.info("=" * 60)
    
    stats = MigrationStats()
    backup_dir = None
    
    # Create backup directory if requested
    if create_backup and not dry_run:
        backup_dir = create_backup_directory()
    
    try:
        # Get database session
        db = SessionLocal()
        
        try:
            # Get all documents
            logger.info("Fetching all documents from database...")
            documents = get_all(db, Documents)
            stats.total_documents = len(documents)
            logger.info(f"Found {stats.total_documents} documents to process")
            
            if stats.total_documents == 0:
                logger.info("No documents found. Migration complete.")
                return
            
            # Process each document
            logger.info("\nStarting migration process...")
            for idx, document in enumerate(documents, 1):
                logger.info(f"\nProcessing document {idx}/{stats.total_documents} (ID: {document.id})...")
                migrate_document(document, db, stats, dry_run=dry_run, backup_dir=backup_dir)
                
                # Commit every 10 documents (or at the end)
                if idx % 10 == 0 and not dry_run:
                    db.commit()
                    logger.info(f"Committed batch of 10 documents (processed {idx}/{stats.total_documents})")
            
            # Final commit
            if not dry_run:
                db.commit()
                logger.info("Final commit completed")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}", exc_info=True)
            if not dry_run:
                db.rollback()
                logger.error("Database rollback performed due to error")
            raise
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    
    finally:
        # Print summary
        stats.print_summary()
        
        if dry_run:
            logger.info("\n" + "=" * 60)
            logger.info("DRY RUN COMPLETE - No changes were made")
            logger.info("Run with --live flag to perform actual migration")
            logger.info("=" * 60)
        else:
            logger.info("\n" + "=" * 60)
            logger.info("MIGRATION COMPLETE")
            if backup_dir:
                logger.info(f"Backup location: {backup_dir}")
            logger.info("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate documents to new folder structure')
    parser.add_argument(
        '--live',
        action='store_true',
        help='Perform actual migration (default is dry-run)'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup (not recommended)'
    )
    
    args = parser.parse_args()
    
    dry_run = not args.live
    create_backup = not args.no_backup
    
    if not dry_run:
        response = input("⚠️  WARNING: This will modify files and database. Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Migration cancelled by user")
            sys.exit(0)
    
    main(dry_run=dry_run, create_backup=create_backup)

