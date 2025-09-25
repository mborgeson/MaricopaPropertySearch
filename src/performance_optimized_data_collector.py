#!/usr/bin/env python
"""
Performance-Optimized Data Collector
CONSOLIDATED - Now imports from unified_data_collector.py

This file maintains backward compatibility while delegating all functionality
to the unified data collector that consolidates features from:
- performance_optimized_data_collector.py (original)
- automatic_data_collector.py
- background_data_collector.py
- improved_automatic_data_collector.py
"""
import logging

from .logging_config import get_logger, get_performance_logger

# Import all functionality from the unified collector
from .unified_data_collector import (
    BackgroundDataCollectionManager,
    BackgroundDataWorker,
    CollectionTask,
    DataCollectionCache,
    DataCollectionJob,
    DataCollectionStats,
    JobPriority,
    ProgressiveResults,
)
from .unified_data_collector import (
    UnifiedDataCollector as PerformanceOptimizedDataCollector,  # Main classes; Data structures; Convenience functions
)
from .unified_data_collector import (
    WebScrapingFallback,
    create_background_manager,
    create_unified_collector,
    start_background_collection,
)

logger = get_logger(__name__)

# Backward compatibility message
logger.info(
    "Performance-Optimized Data Collector: Using unified data collector with consolidated features"
)

# Export all the same interface for backward compatibility
__all__ = [
    "PerformanceOptimizedDataCollector",
    "BackgroundDataCollectionManager",
    "BackgroundDataWorker",
    "WebScrapingFallback",
    "CollectionTask",
    "ProgressiveResults",
    "DataCollectionJob",
    "DataCollectionStats",
    "DataCollectionCache",
    "JobPriority",
    "create_unified_collector",
    "create_background_manager",
    "start_background_collection",
]
