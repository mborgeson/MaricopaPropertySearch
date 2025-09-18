#!/usr/bin/env python
"""
Automatic Data Collector - DEPRECATED
CONSOLIDATED into unified_data_collector.py

This file provides backward compatibility imports.
All functionality has been integrated into the unified data collector.
"""

import logging
from .unified_data_collector import UnifiedDataCollector

logger = logging.getLogger(__name__)
logger.warning("automatic_data_collector.py is deprecated. Use unified_data_collector.py instead.")

# Backward compatibility class alias
class MaricopaDataCollector:
    """Backward compatibility wrapper for automatic data collector functionality"""

    def __init__(self, db_manager):
        # Create unified collector instance
        from .enhanced_config_manager import EnhancedConfigManager
        config_manager = EnhancedConfigManager()
        self.unified_collector = UnifiedDataCollector(db_manager, config_manager)
        self.db_manager = db_manager
        logger.info("MaricopaDataCollector: Using unified data collector for automatic data collection")

    async def collect_all_data_for_apn(self, apn: str):
        """Collect comprehensive data using unified collector"""
        logger.info(f"Automatic data collection (via unified collector) for APN: {apn}")
        result = await self.unified_collector.collect_property_data_progressive(apn)

        # Convert to expected format
        return {
            'apn': apn,
            'tax_data_collected': 'tax_info' in result.data,
            'sales_data_collected': 'sales_history' in result.data,
            'tax_records': result.data.get('tax_info', []),
            'sales_records': result.data.get('sales_history', []),
            'errors': result.errors
        }

    def collect_data_for_apn_sync(self, apn: str):
        """Synchronous wrapper for automatic data collection"""
        return self.unified_collector.collect_data_for_apn_sync(apn)

# Export for backward compatibility
__all__ = ['MaricopaDataCollector']