#!/usr/bin/env python3
"""
Script to run the Phase 4 migrations for the Metis RAG Authentication Implementation Plan.
This script runs the Alembic migrations to add the roles, user-role associations, 
notifications, organizations, and organization-member tables.
"""

import asyncio
import sys
import os
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the project root directory
project_root = Path(__file__).parent.parent.absolute()


async def run_migrations():
    """Run the Alembic migrations"""
    logger.info("Running Alembic migrations for Phase 4...")
    
    # Change to the project root directory
    os.chdir(project_root)
    
    try:
        # Run the migrations
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info(f"Migration output:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"Migration warnings/errors:\n{result.stderr}")
        
        logger.info("Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed with exit code {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        return False


async def main():
    """Main function"""
    logger.info("Starting Phase 4 migrations...")
    
    # Run the migrations
    success = await run_migrations()
    
    if success:
        logger.info("Phase 4 migrations completed successfully")
        logger.info("The following tables have been added:")
        logger.info("  - roles: For role-based access control")
        logger.info("  - user_roles: For user-role associations")
        logger.info("  - notifications: For the notification system")
        logger.info("  - organizations: For multi-tenant isolation")
        logger.info("  - organization_members: For organization membership")
        logger.info("The documents table has been updated with an organization_id column")
    else:
        logger.error("Phase 4 migrations failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())