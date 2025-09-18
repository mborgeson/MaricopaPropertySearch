"""
Simple Data Collection Cache
"""

import json
from pathlib import Path
from datetime import datetime

class DataCollectionCache:
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.property_cache = {}
        self.tax_cache = {}
        self.sales_cache = {}
        self.logger = None

    def clear_apn_cache(self, apn):
        """Clear cache for specific APN"""
        if apn in self.property_cache:
            del self.property_cache[apn]
        if apn in self.tax_cache:
            del self.tax_cache[apn]
        if apn in self.sales_cache:
            del self.sales_cache[apn]
        return True

    def is_cached(self, apn):
        """Check if data for given APN exists in cache

        Args:
            apn (str): The APN to check for in cache

        Returns:
            bool: True if APN data exists in any cache, False otherwise
        """
        if not apn or not isinstance(apn, str):
            return False

        # Check if APN exists in any of the cache dictionaries
        return (apn in self.property_cache or
                apn in self.tax_cache or
                apn in self.sales_cache)

    def save_cache(self):
        """Save cache to disk"""
        pass
