#!/usr/bin/env python
"""
Run the migration to add the memories table
"""
import asyncio
import logging
import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import command
from alembic.config import Config
from app.core.config import SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the migration to add the memories table"""
    try:
        logger.info("Starting memory table migration")
        
        # Get the alembic.ini path
        alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini')
        
        # Create Alembic config
        alembic_cfg = Config(alembic_ini_path)
        
        # Run the migration
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Memory table migration completed successfully")
    except Exception as e:
        logger.error(f"Error running memory table migration: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info(f"Using database URL: {SETTINGS.database_url}")
    asyncio.run(run_migration())