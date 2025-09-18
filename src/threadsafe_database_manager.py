#!/usr/bin/env python
"""
Thread-Safe Database Manager
CONSOLIDATED - Now imports from database_manager_unified.py

This file maintains backward compatibility while delegating all functionality
to the unified database manager that consolidates features from:
- database_manager.py (base implementation)
- threadsafe_database_manager.py (advanced features)
"""

# Import all functionality from the unified manager
from .database_manager_unified import (
    # Main class
    UnifiedDatabaseManager as ThreadSafeDatabaseManager,
    # Aliases for backward compatibility
    DatabaseManager,
)

import logging
from .logging_config import get_logger

logger = get_logger(__name__)

# Backward compatibility message
logger.info(
    "Thread-Safe Database Manager: Using unified database manager with consolidated features"
)

# Export all the same interface for backward compatibility
__all__ = [
    "ThreadSafeDatabaseManager",
    "DatabaseManager",
]
