#!/usr/bin/env python
"""
Background Data Collection System - DEPRECATED
CONSOLIDATED into unified_data_collector.py

This file provides backward compatibility imports.
All functionality has been integrated into the unified data collector.
"""

import logging

logger = logging.getLogger(__name__)
logger.warning("background_data_collector.py is deprecated. Use unified_data_collector.py instead.")

# Import all functionality from unified collector
from .unified_data_collector import (
    BackgroundDataCollectionManager,
    BackgroundDataWorker,
    DataCollectionJob,
    DataCollectionStats,
    DataCollectionCache,
    JobPriority,
    create_background_manager,
    start_background_collection
)

logger.info("Background data collector: Using unified data collector for background processing")

# Export all the same interface for backward compatibility
__all__ = [
    'BackgroundDataCollectionManager',
    'BackgroundDataWorker',
    'DataCollectionJob',
    'DataCollectionStats',
    'DataCollectionCache',
    'JobPriority',
    'create_background_manager',
    'start_background_collection'
]