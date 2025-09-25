#!/usr/bin/env python
"""
Improved Automatic Data Collector - DEPRECATED
CONSOLIDATED into unified_data_collector.py

This file provides backward compatibility imports.
All functionality has been integrated into the unified data collector.
"""
import logging

logger = logging.getLogger(__name__)
logger.warning(
    "improved_automatic_data_collector.py is deprecated. Use unified_data_collector.py instead."
)

# Backward compatibility class alias
from .unified_data_collector import UnifiedDataCollector


class ImprovedMaricopaDataCollector:
    """Backward compatibility wrapper for improved automatic data collector functionality"""

    def __init__(self, db_manager, api_client):
        # Create unified collector instance - it will create its own API client
        from .enhanced_config_manager import EnhancedConfigManager

        config_manager = EnhancedConfigManager()
        self.unified_collector = UnifiedDataCollector(db_manager, config_manager)
        self.db_manager = db_manager
        self.api_client = api_client  # Keep reference for compatibility
        logger.info(
            "ImprovedMaricopaDataCollector: Using unified data collector for comprehensive data collection"
        )


def collect_data_for_apn_sync(self, apn: str):
    """
    Comprehensive data collection using unified collector
    Runs ALL Maricopa County organization scripts automatically
    """
    logger.info(
        f"Improved automatic data collection (via unified collector) for APN: {apn}"
    )
    return self.unified_collector.collect_data_for_apn_sync(apn)


# Export for backward compatibility
__all__ = ["ImprovedMaricopaDataCollector"]
