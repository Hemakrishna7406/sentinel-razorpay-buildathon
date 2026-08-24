#!/usr/bin/env python3
"""
Sentinel — Audit Chain Verifier

This script loads all audit records from the PostgreSQL database in chronological order
and validates the cryptographic hashes. 

If any record was tampered with (modified or deleted), the chain will break because
record_hash_N = SHA256(payload_N || record_hash_N-1).
"""

import sys
import logging
from db.database import SessionLocal
from db.models import AuditRecord
from security.audit_chain import verify_audit_chain

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Connecting to database...")
    db = SessionLocal()
    try:
        logger.info("Fetching audit records...")
        records = db.query(AuditRecord).order_by(AuditRecord.id).all()
        
        if not records:
            logger.info("No audit records found. Chain is trivially valid.")
            sys.exit(0)
            
        logger.info(f"Verifying {len(records)} audit records...")
        
        valid, checked, invalid_ids = verify_audit_chain(records)
        
        if valid:
            logger.info(f"✅ SUCCESS: Verified {checked} contiguous records.")
            logger.info("The audit chain is intact. No tampering detected.")
            sys.exit(0)
        else:
            logger.error(f"❌ FAILED: Tampering detected in the audit chain!")
            logger.error(f"Number of valid records checked before failure or total records: {checked}")
            logger.error(f"Invalid Record IDs: {invalid_ids}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Verification failed due to an error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
