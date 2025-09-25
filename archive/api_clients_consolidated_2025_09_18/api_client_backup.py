"""
Maricopa County API Client
Handles communication with Maricopa County property assessment API
"""

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

# Import centralized logging
from logging_config import (
    get_api_logger,
    get_logger,
    get_performance_logger,
    log_exception,
)

logger = get_logger(__name__)
perf_logger = get_performance_logger(__name__)
api_logger = get_api_logger(__name__)


class MaricopaAPIClient:
    def __init__(self, config_manager):
        logger.info("Initializing Maricopa API Client")

        self.config = config_manager.get_api_config()
        self.base_url = self.config["base_url"]
        self.token = self.config["token"]
        self.timeout = self.config["timeout"]
        self.max_retries = self.config["max_retries"]

        logger.debug(
            f"API Configuration - Base URL: {self.base_url}, Timeout: {self.timeout}s, Max Retries: {self.max_retries}"
        )

        self.session = requests.Session()
        # Use the actual API header format from the documentation
        self.session.headers.update(
            {
                "User-Agent": None,  # API docs specify null user-agent
                "Accept": "application/json",
                "AUTHORIZATION": (
                    self.token if self.token else None
                ),  # Custom header name
            }
        )

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        logger.info("Maricopa API Client initialized successfully")

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def _make_request(
        self, endpoint: str, params: Dict = None, retry_count: int = 0
    ) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        self._rate_limit()

        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                if retry_count < self.max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    return None
            else:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                return self._make_request(endpoint, params, retry_count + 1)
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {e}")
            if retry_count < self.max_retries:
                return self._make_request(endpoint, params, retry_count + 1)
            return None

    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Search properties by owner name using the real API"""
        logger.info(f"Searching properties by owner: {owner_name}")

        # Use the actual API endpoint from documentation
        params = {"q": owner_name}
        results = []
        page = 1

        while len(results) < limit:
            if page > 1:
                params["page"] = page

            response = self._make_request("/search/property/", params)

            if not response:
                break

            # Extract real property data from API response
            properties = response.get("RealProperty", [])
            if not properties:
                break

            # Process and clean the data
            for prop in properties:
                if len(results) >= limit:
                    break

                cleaned_prop = self._clean_property_data(prop)
                if cleaned_prop and self._is_owner_match(cleaned_prop, owner_name):
                    results.append(cleaned_prop)

            # Check if there are more pages
            total_found = response.get("TotalFound", 0)
            if (
                len(results) >= total_found or len(properties) < 25
            ):  # API returns 25 per page
                break

            page += 1

        logger.info(f"Found {len(results)} properties for owner: {owner_name}")
        return results[:limit]

    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Search properties by address using the real API"""
        logger.info(f"Searching properties by address: {address}")

        params = {"q": address}
        results = []
        page = 1

        while len(results) < limit:
            if page > 1:
                params["page"] = page

            response = self._make_request("/search/property/", params)

            if not response:
                break

            properties = response.get("RealProperty", [])
            if not properties:
                break

            for prop in properties:
                if len(results) >= limit:
                    break

                cleaned_prop = self._clean_property_data(prop)
                if cleaned_prop and self._is_address_match(cleaned_prop, address):
                    results.append(cleaned_prop)

            total_found = response.get("TotalFound", 0)
            if len(results) >= total_found or len(properties) < 25:
                break

            page += 1

        logger.info(f"Found {len(results)} properties for address: {address}")
        return results[:limit]

    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Search property by APN using the real API"""
        logger.info(f"Searching property by APN: {apn}")

        # Clean and format APN
        clean_apn = self._format_apn(apn)

        # Use the parcel details endpoint
        response = self._make_request(f"/parcel/{clean_apn}")

        if response:
            logger.info(f"Found property for APN: {apn}")
            return self._clean_property_data(response)
        else:
            logger.warning(f"No property found for APN: {apn}")
            return None

    def get_property_details(self, apn: str) -> Optional[Dict]:
        """Get detailed property information using multiple API endpoints"""
        logger.info(f"Getting property details for APN: {apn}")

        clean_apn = self._format_apn(apn)

        # Collect data from multiple endpoints
        property_data = {}

        # Get basic parcel data
        basic_data = self._make_request(f"/parcel/{clean_apn}")
        if basic_data:
            property_data.update(self._clean_property_data(basic_data))

        # Get property info
        prop_info = self._make_request(f"/parcel/{clean_apn}/propertyinfo")
        if prop_info:
            property_data.update(self._extract_property_info(prop_info))

        # Get address data
        address_data = self._make_request(f"/parcel/{clean_apn}/address")
        if address_data:
            property_data.update(self._extract_address_info(address_data))

        # Get residential details if applicable
        residential_data = self._make_request(
            f"/parcel/{clean_apn}/residential-details"
        )
        if residential_data:
            property_data.update(self._extract_residential_info(residential_data))

        # Get owner details
        owner_data = self._make_request(f"/parcel/{clean_apn}/owner-details")
        if owner_data:
            property_data.update(self._extract_owner_info(owner_data))

        if property_data:
            logger.info(f"Retrieved comprehensive property details for APN: {apn}")
            return property_data
        else:
            logger.warning(f"No property details found for APN: {apn}")
            return None

    def get_tax_history(self, apn: str, years: int = 5) -> List[Dict]:
        """Get tax/valuation history for property using the real API"""
        logger.info(f"Getting tax history for APN: {apn}")

        clean_apn = self._format_apn(apn)

        # Use the valuations endpoint
        response = self._make_request(f"/parcel/{clean_apn}/valuations")

        if response:
            tax_history = self._extract_valuation_history(response)
            logger.info(
                f"Retrieved {len(tax_history)} valuation records for APN: {apn}"
            )
            return tax_history
        else:
            logger.warning(f"No tax history found for APN: {apn}")
            return []

    def get_sales_history(self, apn: str, years: int = 10) -> List[Dict]:
        """Get sales history for property (Note: API may not provide sales history directly)"""
        logger.info(f"Getting sales history for APN: {apn}")

        # The Maricopa API doesn't appear to have a direct sales history endpoint
        # This would require web scraping or additional data sources
        logger.warning(f"Sales history not available through API for APN: {apn}")
        return []

    def get_property_documents(self, apn: str) -> List[Dict]:
        """Get property documents"""
        logger.info(f"Getting property documents for APN: {apn}")

        response = self._make_request(f"/api/properties/{apn}/documents")

        if response and "documents" in response:
            logger.info(
                f"Retrieved {len(response['documents'])} documents for APN: {apn}"
            )
            return response["documents"]
        else:
            logger.warning(f"No documents found for APN: {apn}")
            return []

    def bulk_property_search(self, apns: List[str]) -> Dict[str, Dict]:
        """Bulk search for multiple properties"""
        logger.info(f"Bulk searching {len(apns)} properties")

        # Split into batches to avoid overwhelming the API
        batch_size = 20
        results = {}

        for i in range(0, len(apns), batch_size):
            batch = apns[i : i + batch_size]

            params = {"apns": ",".join(batch)}
            response = self._make_request("/api/properties/bulk", params)

            if response and "properties" in response:
                results.update(response["properties"])

            # Small delay between batches
            if i + batch_size < len(apns):
                time.sleep(0.5)

        logger.info(f"Bulk search completed: {len(results)} properties retrieved")
        return results

    def validate_apn(self, apn: str) -> bool:
        """Validate if APN exists in the system"""
        logger.debug(f"Validating APN: {apn}")

        response = self._make_request(f"/api/properties/{apn}/validate")

        if response:
            return response.get("valid", False)
        return False

    def get_api_status(self) -> Dict[str, Any]:
        """Get API service status by testing a simple endpoint"""
        try:
            # Test with a simple search to verify API connectivity
            response = self._make_request("/search/property/", {"q": "test"})

            if response is not None:
                return {
                    "status": "connected",
                    "version": "unknown",
                    "base_url": self.base_url,
                    "authenticated": bool(self.token),
                }
            else:
                return {"status": "error", "error": "API request failed"}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    def _format_apn(self, apn: str) -> str:
        """Format APN for API calls"""
        # Remove any spaces, dashes, or dots as the API can handle various formats
        return apn.replace(" ", "").replace("-", "").replace(".", "")

    def _is_owner_match(self, property_data: Dict, owner_name: str) -> bool:
        """Check if property owner matches search term"""
        prop_owner = property_data.get("owner_name", "").lower()
        search_owner = owner_name.lower()
        return search_owner in prop_owner or prop_owner in search_owner

    def _is_address_match(self, property_data: Dict, address: str) -> bool:
        """Check if property address matches search term"""
        prop_address = property_data.get("property_address", "").lower()
        search_address = address.lower()
        return search_address in prop_address or prop_address in search_address

    def _clean_property_data(self, raw_data: Dict) -> Dict:
        """Clean and standardize property data from API response"""
        if not raw_data:
            return {}

        cleaned = {
            "apn": raw_data.get("APN", raw_data.get("ParcelNumber", "")),
            "owner_name": raw_data.get("OwnerName", ""),
            "property_address": self._format_address(raw_data),
            "mailing_address": raw_data.get("MailingAddress", ""),
            "legal_description": raw_data.get("LegalDescription", ""),
            "land_use_code": raw_data.get("LandUseCode", ""),
            "year_built": self._safe_int(raw_data.get("YearBuilt")),
            "living_area_sqft": self._safe_int(raw_data.get("LivingArea")),
            "lot_size_sqft": self._safe_float(raw_data.get("LotSize")),
            "bedrooms": self._safe_int(raw_data.get("Bedrooms")),
            "bathrooms": self._safe_float(raw_data.get("Bathrooms")),
            "pool": raw_data.get("Pool", "").lower() == "yes",
            "garage_spaces": self._safe_int(raw_data.get("Garage")),
            "latest_assessed_value": self._safe_float(raw_data.get("AssessedValue")),
        }

        # Remove None values
        return {k: v for k, v in cleaned.items() if v is not None}

    def _format_address(self, raw_data: Dict) -> str:
        """Format property address from various API fields"""
        address_parts = []

        # Try different address field names
        street_num = raw_data.get("StreetNumber", raw_data.get("HouseNumber", ""))
        street_name = raw_data.get("StreetName", "")
        city = raw_data.get("City", "Phoenix")  # Default to Phoenix
        state = raw_data.get("State", "AZ")
        zip_code = raw_data.get("ZipCode", raw_data.get("Zip", ""))

        if street_num:
            address_parts.append(str(street_num))
        if street_name:
            address_parts.append(street_name)
        if city:
            address_parts.append(city)
        if state:
            address_parts.append(state)
        if zip_code:
            address_parts.append(str(zip_code))

        return (
            " ".join(address_parts)
            if address_parts
            else raw_data.get("PropertyAddress", "")
        )

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if value is None or value == "":
            return None
        try:
            # Handle string values that might have commas or other formatting
            clean_value = str(value).replace(",", "").replace("$", "").strip()
            return int(float(clean_value))
        except (ValueError, TypeError):
            return None

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == "":
            return None
        try:
            clean_value = str(value).replace(",", "").replace("$", "").strip()
            return float(clean_value)
        except (ValueError, TypeError):
            return None

    def _extract_property_info(self, prop_info: Dict) -> Dict:
        """Extract property information from propertyinfo endpoint"""
        return {
            "land_use_code": prop_info.get("LandUseCode", ""),
            "year_built": self._safe_int(prop_info.get("YearBuilt")),
            "living_area_sqft": self._safe_int(prop_info.get("LivingArea")),
            "lot_size_sqft": self._safe_float(prop_info.get("LotSize")),
        }

    def _extract_address_info(self, address_data: Dict) -> Dict:
        """Extract address information from address endpoint"""
        return {"property_address": self._format_address(address_data)}

    def _extract_residential_info(self, residential_data: Dict) -> Dict:
        """Extract residential details from residential-details endpoint"""
        return {
            "bedrooms": self._safe_int(residential_data.get("Bedrooms")),
            "bathrooms": self._safe_float(residential_data.get("Bathrooms")),
            "pool": residential_data.get("Pool", "").lower() == "yes",
            "garage_spaces": self._safe_int(residential_data.get("Garage")),
        }

    def _extract_owner_info(self, owner_data: Dict) -> Dict:
        """Extract owner information from owner-details endpoint"""
        return {
            "owner_name": owner_data.get("OwnerName", ""),
            "mailing_address": owner_data.get("MailingAddress", ""),
        }

    def _extract_valuation_history(self, valuation_data: Dict) -> List[Dict]:
        """Extract valuation history from valuations endpoint"""
        valuations = valuation_data.get("Valuations", [])
        tax_history = []

        for val in valuations:
            record = {
                "tax_year": self._safe_int(val.get("TaxYear")),
                "assessed_value": self._safe_float(val.get("AssessedValue")),
                "limited_value": self._safe_float(val.get("LimitedValue")),
                "tax_amount": self._safe_float(val.get("TaxAmount")),
                "payment_status": val.get("PaymentStatus", "Unknown"),
            }
            if record["tax_year"]:
                tax_history.append(record)

        return tax_history

    def close(self):
        """Close the HTTP session"""
        if self.session:
            self.session.close()
            logger.info("API client session closed")


class MockMaricopaAPIClient(MaricopaAPIClient):
    """Mock API client for testing and development"""

    def __init__(self, config_manager):
        # Initialize parent but don't actually make HTTP requests
        self.config = config_manager.get_api_config()
        self.base_url = self.config["base_url"]
        self.token = self.config["token"]

        logger.info("Using Mock API Client - no actual API calls will be made")

    def _generate_mock_property(self, apn: str) -> Dict:
        """Generate mock property data"""
        import random

        return {
            "apn": apn,
            "owner_name": f"Mock Owner {apn[-4:]}",
            "property_address": f"{random.randint(100, 9999)} Mock Street, Phoenix, AZ 8510{random.randint(1, 9)}",
            "mailing_address": f"PO Box {random.randint(1000, 9999)}, Phoenix, AZ 8510{random.randint(1, 9)}",
            "legal_description": f"Mock Legal Description for {apn}",
            "land_use_code": random.choice(["R1", "R2", "C1", "I1"]),
            "year_built": random.randint(1950, 2023),
            "living_area_sqft": random.randint(800, 5000),
            "lot_size_sqft": random.randint(5000, 20000),
            "bedrooms": random.randint(2, 6),
            "bathrooms": random.randint(1, 4),
            "pool": random.choice([True, False]),
            "garage_spaces": random.randint(0, 3),
        }

    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Mock search by APN"""
        logger.info(f"Mock: Searching property by APN: {apn}")
        return self._generate_mock_property(apn)

    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Mock search by owner"""
        logger.info(f"Mock: Searching properties by owner: {owner_name}")
        return [
            self._generate_mock_property(f"12345{i:03d}") for i in range(min(3, limit))
        ]

    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Mock search by address"""
        logger.info(f"Mock: Searching properties by address: {address}")
        return [
            self._generate_mock_property(f"67890{i:03d}") for i in range(min(2, limit))
        ]

    def get_api_status(self) -> Dict[str, Any]:
        """Mock API status"""
        return {
            "status": "mock",
            "version": "1.0.0-mock",
            "rate_limit": {"requests_per_minute": 60},
            "endpoints": ["mock_endpoints"],
        }
