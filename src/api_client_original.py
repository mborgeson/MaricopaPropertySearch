"""
Maricopa County API Client - Updated with comprehensive logging
Handles communication with Maricopa County property assessment API
"""

import requests
import time
import logging
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from src.logging_config import get_api_logger

logger = logging.getLogger(__name__)
api_logger = get_api_logger(__name__)

class MaricopaAPIClient:
    def __init__(self, config_manager):
        logger.info("Initializing Maricopa API Client")
        
        self.config = config_manager.get_api_config()
        self.base_url = self.config['base_url']
        self.token = self.config['token']
        self.timeout = self.config['timeout']
        self.max_retries = self.config['max_retries']
        
        logger.debug(f"API Configuration - Base URL: {self.base_url}, Timeout: {self.timeout}s, Max Retries: {self.max_retries}")
        
        self.session = requests.Session()
        # Use the actual API header format from the documentation
        self.session.headers.update({
            'User-Agent': None,  # API docs specify null user-agent
            'Accept': 'application/json',
            'AUTHORIZATION': self.token if self.token else None  # Custom header name
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info("Maricopa API Client initialized successfully")
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None, retry_count: int = 0) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        self._rate_limit()
        
        url = urljoin(self.base_url, endpoint)
        logger.debug(f"Making API request to: {url}")
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            logger.debug(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry (attempt {retry_count + 1})")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, params, retry_count + 1)
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    return None
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                logger.info(f"Retrying after timeout (attempt {retry_count + 1})")
                return self._make_request(endpoint, params, retry_count + 1)
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for {url}: {e}")
            if retry_count < self.max_retries:
                logger.info(f"Retrying after exception (attempt {retry_count + 1})")
                return self._make_request(endpoint, params, retry_count + 1)
            return None
    
    # @api_logger.log_api_call('/api/properties/search/owner', 'GET')
    # @perf_logger.log_performance('search_by_owner')
    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Search properties by owner name using real Maricopa API"""
        logger.info(f"Searching properties by owner: {owner_name} (limit: {limit})")
        
        params = {
            'q': owner_name
        }
        
        try:
            response = self._make_request('/search/property/', params)
            
            if response and 'Results' in response:
                results = response['Results'][:limit]  # Limit results
                normalized_results = [self._normalize_api_data(result) for result in results]
                result_count = len(normalized_results)
                logger.info(f"Found {result_count} properties for owner: {owner_name}")
                
                # Log search analytics
                logger.info(f"SEARCH_ANALYTICS: owner_search, results={result_count}, limit={limit}")
                
                return normalized_results
            else:
                logger.warning(f"No properties found for owner: {owner_name}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching properties by owner {owner_name}: {e}")
            raise
    
    # @api_logger.log_api_call('/api/properties/search/address', 'GET')
    # @perf_logger.log_performance('search_by_address')
    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Search properties by address using real Maricopa API"""
        logger.info(f"Searching properties by address: {address} (limit: {limit})")
        
        params = {
            'q': address
        }
        
        try:
            response = self._make_request('/search/property/', params)
            
            if response and 'Results' in response:
                results = response['Results'][:limit]  # Limit results
                normalized_results = [self._normalize_api_data(result) for result in results]
                result_count = len(normalized_results)
                logger.info(f"Found {result_count} properties for address: {address}")
                
                # Log search analytics
                logger.info(f"SEARCH_ANALYTICS: address_search, results={result_count}, limit={limit}")
                
                return normalized_results
            else:
                logger.warning(f"No properties found for address: {address}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching properties by address {address}: {e}")
            raise
    
    # @api_logger.log_api_call('/api/properties/{apn}', 'GET')
    # @perf_logger.log_performance('search_by_apn')
    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Search property by APN using real Maricopa API"""
        logger.info(f"Searching property by APN: {apn}")
        
        try:
            params = {'q': apn}
            response = self._make_request('/search/property/', params)
            
            if response and 'Results' in response and len(response['Results']) > 0:
                # Find exact APN match in results
                for result in response['Results']:
                    if result.get('APN', '').replace('-', '').replace('.', '') == apn.replace('-', '').replace('.', ''):
                        normalized_result = self._normalize_api_data(result)
                        logger.info(f"Found property for APN: {apn}")
                        logger.info(f"SEARCH_ANALYTICS: apn_search, results=1, apn={apn}")
                        return normalized_result
                
                # If no exact match, return first result
                if response['Results']:
                    normalized_result = self._normalize_api_data(response['Results'][0])
                    logger.info(f"Found similar property for APN: {apn}")
                    logger.info(f"SEARCH_ANALYTICS: apn_search, results=1, apn={apn}")
                    return normalized_result
            
            logger.warning(f"No property found for APN: {apn}")
            logger.info(f"SEARCH_ANALYTICS: apn_search, results=0, apn={apn}")
            return None
                
        except Exception as e:
            logger.error(f"Error searching property by APN {apn}: {e}")
            raise
    
    # @api_logger.log_api_call('/api/properties/{apn}/details', 'GET')
    # @perf_logger.log_performance('get_property_details')
    def get_property_details(self, apn: str) -> Optional[Dict]:
        """Get detailed property information using comprehensive API endpoints"""
        logger.info(f"Getting property details for APN: {apn}")
        
        try:
            # Use the comprehensive property data method
            detailed_info = self.get_comprehensive_property_info(apn)
            
            if detailed_info:
                logger.info(f"Retrieved property details for APN: {apn}")
                return detailed_info
            else:
                logger.warning(f"No property details found for APN: {apn}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting property details for APN {apn}: {e}")
            raise
    
    # @api_logger.log_api_call('/api/properties/{apn}/tax-history', 'GET')
    # @perf_logger.log_performance('get_tax_history')
    def get_tax_history(self, apn: str, years: int = 5) -> List[Dict]:
        """Get tax history using valuation endpoint"""
        logger.info(f"Getting tax history for APN: {apn} (years: {years})")
        
        try:
            response = self._make_request(f'/parcel/{apn}/valuations/')
            
            if response and isinstance(response, list):
                # Filter by years if requested
                current_year = 2024
                min_year = current_year - years + 1
                
                filtered_records = [
                    record for record in response 
                    if record.get('TaxYear') and int(record.get('TaxYear', 0)) >= min_year
                ]
                
                result_count = len(filtered_records)
                logger.info(f"Retrieved {result_count} tax records for APN: {apn}")
                return filtered_records
            else:
                logger.warning(f"No tax history found for APN: {apn}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting tax history for APN {apn}: {e}")
            raise
    
    # @api_logger.log_api_call('/api/properties/{apn}/sales-history', 'GET')
    # @perf_logger.log_performance('get_sales_history')
    def get_sales_history(self, apn: str, years: int = 10) -> List[Dict]:
        """Get sales history - will need to be implemented via web scraping"""
        logger.info(f"Getting sales history for APN: {apn} (years: {years})")
        logger.warning(f"Sales history requires web scraping from Recorder's office - not available via API")
        
        # For now, return empty list as sales data requires scraping
        # TODO: Implement recorder web scraping
        return []
    
    # @api_logger.log_api_call('/api/properties/{apn}/documents', 'GET')
    # @perf_logger.log_performance('get_property_documents')
    def get_property_documents(self, apn: str) -> List[Dict]:
        """Get property documents - will need to be implemented via web scraping"""
        logger.info(f"Getting property documents for APN: {apn}")
        logger.warning(f"Property documents require web scraping from Recorder's office - not available via API")
        
        # For now, return empty list as documents require scraping
        # TODO: Implement recorder web scraping
        return []
    
    # @api_logger.log_api_call('/api/properties/bulk', 'GET')
    # @perf_logger.log_performance('bulk_property_search')
    def bulk_property_search(self, apns: List[str]) -> Dict[str, Dict]:
        """Bulk search for multiple properties using individual API calls"""
        logger.info(f"Starting bulk search for {len(apns)} properties")
        
        results = {}
        
        try:
            for i, apn in enumerate(apns):
                logger.debug(f"Processing APN {i+1}/{len(apns)}: {apn}")
                
                try:
                    property_data = self.search_by_apn(apn)
                    if property_data:
                        results[apn] = property_data
                        logger.debug(f"Found property for APN: {apn}")
                    else:
                        logger.debug(f"No property found for APN: {apn}")
                except Exception as e:
                    logger.warning(f"Error searching APN {apn}: {e}")
                    continue
                
                # Rate limiting - small delay between requests
                if i < len(apns) - 1:
                    time.sleep(0.2)
            
            success_rate = (len(results) / len(apns)) * 100 if apns else 0
            logger.info(f"Bulk search completed: {len(results)}/{len(apns)} properties retrieved ({success_rate:.1f}% success rate)")
            logger.info(f"SEARCH_ANALYTICS: bulk_search, requested={len(apns)}, returned={len(results)}, success_rate={success_rate:.1f}%")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk property search for {len(apns)} APNs: {e}")
            raise
    
    # @perf_logger.log_performance('validate_apn')
    def validate_apn(self, apn: str) -> bool:
        """Validate if APN exists by searching for it"""
        logger.debug(f"Validating APN: {apn}")
        
        try:
            property_data = self.search_by_apn(apn)
            is_valid = property_data is not None
            logger.debug(f"APN {apn} validation result: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating APN {apn}: {e}")
            return False
    
    # @api_logger.log_api_call('/api/status', 'GET')
    def get_api_status(self) -> Dict[str, Any]:
        """Get API service status and limits"""
        logger.debug("Getting API status - real Maricopa County API active")
        
        # Return real API status 
        return {
            'status': 'Real API',
            'version': '2.0',
            'rate_limit': {
                'requests_per_minute': 60,
                'remaining': 60
            },
            'endpoints': ['property', 'tax', 'sales'],
            'message': 'Using real Maricopa County Assessor API'
        }
    
    def _format_apn(self, apn: str) -> str:
        """Format APN for API calls"""
        # Remove any spaces, dashes, or dots as the API can handle various formats
        return apn.replace(' ', '').replace('-', '').replace('.', '')
    
    def close(self):
        """Close the HTTP session"""
        try:
            if self.session:
                self.session.close()
                logger.info("API client session closed successfully")
        except Exception as e:
            logger.error(f"Error closing API client session: {e}")
    
    def _validate_apn(self, apn: str) -> bool:
        """Validate APN format"""
        if not apn or not isinstance(apn, str):
            return False
        
        # Remove formatting and check if it's reasonable length
        clean_apn = self._format_apn(apn)
        return len(clean_apn) >= 8 and clean_apn.replace('-', '').replace('.', '').isdigit()
    
    def _validate_property_data(self, data: Dict) -> Dict:
        """Validate and clean property data"""
        if not data:
            return {}
        
        # Required fields
        required_fields = ['apn']
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"Property data missing required field: {field}")
                return {}
        
        # Clean and validate data types
        validated = {}
        for key, value in data.items():
            if value is not None and value != '':
                validated[key] = value
        
        # Ensure numeric fields are properly typed
        numeric_fields = ['year_built', 'living_area_sqft', 'lot_size_sqft', 'bedrooms', 'garage_spaces']
        float_fields = ['bathrooms', 'latest_assessed_value']
        
        for field in numeric_fields:
            if field in validated:
                validated[field] = self._safe_int(validated[field])
        
        for field in float_fields:
            if field in validated:
                validated[field] = self._safe_float(validated[field])
        
        return validated
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def search_all_property_types(self, query: str, limit: int = 50) -> Dict[str, List[Dict]]:
        """Search all property types and return categorized results"""
        logger.info(f"Searching all property types for: {query} (limit: {limit})")
        
        params = {'q': query}
        results = {
            'real_property': [],
            'business_personal_property': [],
            'mobile_home': [],
            'rental': [],
            'subdivisions': []
        }
        
        endpoints = {
            '/search/rp/': 'real_property',
            '/search/bpp/': 'business_personal_property', 
            '/search/mh/': 'mobile_home',
            '/search/rental/': 'rental',
            '/search/sub/': 'subdivisions'
        }
        
        try:
            for endpoint, category in endpoints.items():
                response = self._make_request(endpoint, params)
                
                if response and 'Results' in response and response.get('TOTAL', 0) > 0:
                    # Normalize API data for database compatibility
                    normalized_results = [self._normalize_api_data(result) for result in response['Results'][:limit]]
                    results[category] = normalized_results
                    logger.debug(f"Found {len(results[category])} {category} results")
            
            total_results = sum(len(results[cat]) for cat in results)
            logger.info(f"Found {total_results} total results across all property types")
            
            return results
                
        except Exception as e:
            logger.error(f"Error searching all property types for {query}: {e}")
            raise
    
    def _normalize_api_data(self, api_data: Dict) -> Dict:
        """Convert API field names to database field names"""
        field_mapping = {
            # API field -> Database field
            'APN': 'apn',
            'MCR': 'mcr',
            'Ownership': 'owner_name',
            'SitusAddress': 'property_address',
            'SitusCity': 'city',
            'SitusZip': 'zip_code',
            'PropertyType': 'property_type',
            'RentalID': 'rental_id',
            'SubdivisonName': 'subdivision_name',
            'SectionTownshipRange': 'section_township_range',
            
            # Business Personal Property fields
            'AccountNo': 'account_number',
            'Name1': 'business_name',
            'Name2': 'business_name_2',
            
            # Additional common fields
            'Address': 'property_address',
            'City': 'city',
            'Zip': 'zip_code',
            'Owner': 'owner_name'
        }
        
        normalized = {}
        
        # Map known fields
        for api_field, db_field in field_mapping.items():
            if api_field in api_data:
                normalized[db_field] = api_data[api_field]
        
        # Keep unmapped fields as-is (lowercased)
        for key, value in api_data.items():
            if key not in field_mapping:
                normalized[key.lower()] = value
        
        # Ensure required fields exist with defaults
        if 'apn' not in normalized and 'APN' in api_data:
            normalized['apn'] = api_data['APN']
        
        # Provide defaults for missing database fields
        default_fields = {
            'mailing_address': None,
            'legal_description': None, 
            'land_use_code': None,
            'year_built': None,
            'living_area_sqft': None,
            'lot_size_sqft': None,
            'bedrooms': None,
            'bathrooms': None,
            'pool': None,
            'garage_spaces': None,
            'raw_data': json.dumps(api_data)  # Store original API response
        }
        
        for field, default_value in default_fields.items():
            if field not in normalized:
                normalized[field] = default_value
        
        logger.debug(f"Normalized API data: {list(normalized.keys())}")
        
        return normalized
    
    def get_detailed_property_data(self, apn: str) -> Dict[str, Any]:
        """Get comprehensive property data including valuations, improvements, and details"""
        logger.info(f"Getting detailed property data for APN: {apn}")
        
        detailed_data = {}
        
        # Define the detailed endpoints discovered from browser analysis
        endpoints = {
            'valuations': f'/parcel/{apn}/valuations/',
            'residential_details': f'/parcel/{apn}/residential-details/',
            'improvements': f'/parcel/{apn}/improvements/',
            'sketches': f'/parcel/{apn}/sketches/',
            'mapids': f'/parcel/{apn}/mapids/'
        }
        
        # Try to get owner name for rental details
        try:
            basic_search = self.search_all_property_types(apn, limit=1)
            owner_name = None
            for category, results in basic_search.items():
                if results and 'owner_name' in results[0]:
                    owner_name = results[0]['owner_name']
                    break
            
            if owner_name:
                endpoints['rental_details'] = f'/parcel/{apn}/rental-details/{owner_name}/'
        except Exception as e:
            logger.debug(f"Could not determine owner name for rental details: {e}")
        
        # Fetch data from each endpoint
        for endpoint_name, endpoint_path in endpoints.items():
            try:
                response = self._make_request(endpoint_path)
                
                if response:
                    detailed_data[endpoint_name] = response
                    logger.debug(f"Successfully retrieved {endpoint_name} data")
                else:
                    logger.warning(f"No data returned from {endpoint_name}")
                    
            except Exception as e:
                logger.error(f"Error retrieving {endpoint_name} for APN {apn}: {e}")
        
        logger.info(f"Retrieved detailed data from {len(detailed_data)} endpoints for APN: {apn}")
        return detailed_data
    
    def get_comprehensive_property_info(self, apn: str) -> Optional[Dict]:
        """Get complete property information combining basic search + detailed data"""
        logger.info(f"Getting comprehensive property info for APN: {apn}")
        
        try:
            # Try to get basic property info first (optional)
            basic_info = None
            try:
                basic_info = self.search_by_apn(apn)
            except Exception as e:
                logger.warning(f"Basic search failed for APN {apn}, continuing with detailed data only: {e}")
            
            # Get detailed data (primary source)
            detailed_data = self.get_detailed_property_data(apn)
            
            if not detailed_data or not any(detailed_data.values()):
                logger.warning(f"No detailed data found for APN: {apn}")
                return None
            
            # Start with basic info if available, otherwise create minimal structure
            if basic_info:
                comprehensive_info = basic_info.copy()
            else:
                comprehensive_info = {
                    'apn': apn,
                    'search_source': 'detailed_endpoints_only'
                }
            
            # Add valuation history
            if 'valuations' in detailed_data and detailed_data['valuations']:
                valuations = detailed_data['valuations']
                if valuations and len(valuations) > 0:
                    latest_val = valuations[0]  # Most recent year
                    comprehensive_info.update({
                        'latest_tax_year': latest_val.get('TaxYear'),
                        'latest_assessed_value': self._safe_int(latest_val.get('FullCashValue')),
                        'latest_limited_value': self._safe_int(latest_val.get('LimitedPropertyValue', '').strip()),
                        'assessment_ratio': self._safe_float(latest_val.get('AssessmentRatioPercentage')),
                        'tax_area_code': latest_val.get('TaxAreaCode'),
                        'property_use_description': latest_val.get('PEPropUseDesc'),
                        'valuation_history': valuations  # Store full history
                    })
            
            # Add residential details
            if 'residential_details' in detailed_data and detailed_data['residential_details']:
                res_details = detailed_data['residential_details']
                comprehensive_info.update({
                    'year_built': self._safe_int(res_details.get('ConstructionYear')),
                    'lot_size_sqft': self._safe_int(res_details.get('LotSize')),
                    'living_area_sqft': self._safe_int(res_details.get('LivableSpace')),
                    'pool': res_details.get('Pool', False),
                    'quality_grade': res_details.get('ImprovementQualityGrade'),
                    'exterior_walls': res_details.get('ExteriorWalls'),
                    'roof_type': res_details.get('RoofType'),
                    'bathrooms': self._safe_int(res_details.get('BathFixtures')),
                    'garage_spaces': self._safe_int(res_details.get('NumberOfGarages')),
                    'parking_details': res_details.get('ParkingDetails')
                })
                
                # Derive land use code from property use description
                if 'property_use_description' in comprehensive_info:
                    use_desc = comprehensive_info['property_use_description']
                    if 'Multiple Family' in use_desc:
                        comprehensive_info['land_use_code'] = 'MFR'  # Multi-Family Residential
                    elif 'Single Family' in use_desc:
                        comprehensive_info['land_use_code'] = 'SFR'  # Single Family Residential
                    elif 'Commercial' in use_desc:
                        comprehensive_info['land_use_code'] = 'COM'  # Commercial
            
            # Add improvements summary
            if 'improvements' in detailed_data and detailed_data['improvements']:
                improvements = detailed_data['improvements']
                if improvements:
                    comprehensive_info['improvements_count'] = len(improvements)
                    comprehensive_info['total_improvement_sqft'] = sum(
                        self._safe_int(imp.get('ImprovementSquareFootage', 0)) or 0
                        for imp in improvements
                    )
                    comprehensive_info['improvements_details'] = improvements
                    
                    # Calculate living area from residential improvements (apartments, townhouses)
                    residential_sqft = sum(
                        self._safe_int(imp.get('ImprovementSquareFootage', 0)) or 0
                        for imp in improvements 
                        if 'Apartment' in imp.get('ImprovementDescription', '') or 
                           'Town House' in imp.get('ImprovementDescription', '') or
                           'Single Family' in imp.get('ImprovementDescription', '')
                    )
                    if residential_sqft > 0 and not comprehensive_info.get('living_area_sqft'):
                        comprehensive_info['living_area_sqft'] = residential_sqft
                    
                    # Count apartment units for bedroom estimation (more accurate than sq ft calculation)
                    apartment_units = sum(
                        1 for imp in improvements 
                        if 'Apartment' in imp.get('ImprovementDescription', '') or 
                           'Town House' in imp.get('ImprovementDescription', '') or
                           'Single Family' in imp.get('ImprovementDescription', '')
                    )
                    if apartment_units > 0 and not comprehensive_info.get('bedrooms'):
                        # Estimate 1-2 bedrooms per unit for multi-family properties
                        estimated_bedrooms = apartment_units * 2  # Conservative estimate
                        comprehensive_info['bedrooms'] = estimated_bedrooms
            
            # Store raw detailed data for future use
            comprehensive_info['detailed_data'] = detailed_data
            
            # Add required database fields if not present from basic search
            if 'owner_name' not in comprehensive_info:
                comprehensive_info['owner_name'] = None
            if 'property_address' not in comprehensive_info:
                comprehensive_info['property_address'] = None
            if 'mailing_address' not in comprehensive_info:
                comprehensive_info['mailing_address'] = None
            if 'legal_description' not in comprehensive_info:
                comprehensive_info['legal_description'] = None
            if 'land_use_code' not in comprehensive_info:
                comprehensive_info['land_use_code'] = None
            if 'bedrooms' not in comprehensive_info:
                comprehensive_info['bedrooms'] = None
            if 'raw_data' not in comprehensive_info:
                from psycopg2.extras import Json
                comprehensive_info['raw_data'] = Json(detailed_data)
            
            logger.info(f"Successfully compiled comprehensive info for APN: {apn}")
            return comprehensive_info
            
        except Exception as e:
            logger.error(f"Error getting comprehensive property info for APN {apn}: {e}")
            return None
    
    def get_complete_property_info_with_tax_scraping(self, apn: str, use_tax_scraping: bool = False) -> Optional[Dict]:
        """
        Get complete property information including scraped tax data from Treasurer's website
        
        Args:
            apn: Property APN to lookup
            use_tax_scraping: Whether to scrape live tax data from treasurer.maricopa.gov
            
        Returns:
            Complete property information with all available data sources
        """
        logger.info(f"Getting complete property info (with tax scraping: {use_tax_scraping}) for APN: {apn}")
        
        try:
            # Start with comprehensive property info from API endpoints
            complete_info = self.get_comprehensive_property_info(apn)
            
            if not complete_info:
                logger.warning(f"No comprehensive property info found for APN: {apn}")
                return None
            
            # Add tax data from scraping if requested
            if use_tax_scraping:
                try:
                    from tax_scraper import MaricopaTaxScraper
                    import asyncio
                    from playwright.async_api import async_playwright
                    
                    # Use Playwright to scrape tax data
                    async def scrape_tax_data():
                        async with async_playwright() as p:
                            browser = await p.chromium.launch(headless=True)
                            page = await browser.new_page()
                            
                            scraper = MaricopaTaxScraper()
                            tax_data = scraper.scrape_tax_data_for_apn(apn, page)
                            
                            await browser.close()
                            return tax_data
                    
                    # Run the async scraping
                    tax_data = asyncio.run(scrape_tax_data())
                    
                    if tax_data:
                        # Integrate tax data with property info
                        owner_info = tax_data.get('owner_info', {})
                        current_tax = tax_data.get('current_tax', {})
                        
                        # Update fields from tax scraping
                        if owner_info.get('owner_name') and not complete_info.get('owner_name'):
                            complete_info['owner_name'] = owner_info['owner_name']
                        if owner_info.get('property_address') and not complete_info.get('property_address'):
                            complete_info['property_address'] = owner_info['property_address']
                        if owner_info.get('mailing_address') and not complete_info.get('mailing_address'):
                            complete_info['mailing_address'] = owner_info['mailing_address']
                        
                        # Add current tax information
                        complete_info.update({
                            'current_tax_amount': current_tax.get('assessed_tax'),
                            'current_payment_status': current_tax.get('payment_status'),
                            'current_amount_due': current_tax.get('total_due'),
                            'tax_scrape_data': tax_data
                        })
                        
                        logger.info(f"Successfully integrated tax data for APN: {apn}")
                    else:
                        logger.warning(f"Could not scrape tax data for APN: {apn}")
                        
                except Exception as e:
                    logger.error(f"Error scraping tax data for APN {apn}: {e}")
                    # Continue without tax data rather than failing completely
            
            return complete_info
            
        except Exception as e:
            logger.error(f"Error getting complete property info for APN {apn}: {e}")
            return None
    
    def get_complete_property_with_automatic_data_collection(self, apn: str, db_manager) -> Optional[Dict]:
        """
        Get complete property information with automatic tax and sales data collection
        This method automatically collects missing data for any APN
        """
        logger.info(f"Getting complete property data with automatic collection for APN: {apn}")
        
        try:
            # First get basic property information
            property_info = self.search_by_apn(apn)
            if not property_info:
                logger.warning(f"No basic property info found for APN: {apn}")
                return None
            
            # Check what data already exists in database
            existing_tax_records = db_manager.get_tax_history(apn)
            existing_sales_records = db_manager.get_sales_history(apn)
            
            logger.info(f"Existing data - Tax records: {len(existing_tax_records)}, Sales records: {len(existing_sales_records)}")
            
            # Collect missing data automatically
            needs_tax_data = len(existing_tax_records) == 0
            needs_sales_data = len(existing_sales_records) == 0
            
            if needs_tax_data or needs_sales_data:
                logger.info(f"APN {apn} needs data collection - Tax: {needs_tax_data}, Sales: {needs_sales_data}")
                
                # Import and use the automatic data collector
                try:
                    from automatic_data_collector import MaricopaDataCollector
                    
                    collector = MaricopaDataCollector(db_manager)
                    collection_results = collector.collect_data_for_apn_sync(apn)
                    
                    logger.info(f"Data collection completed for APN {apn}: "
                              f"Tax: {collection_results.get('tax_data_collected', False)}, "
                              f"Sales: {collection_results.get('sales_data_collected', False)}")
                    
                    # Add collection results to property info
                    property_info['automatic_collection_results'] = collection_results
                    
                except ImportError:
                    logger.warning("Automatic data collector not available")
                except Exception as e:
                    logger.error(f"Error during automatic data collection: {e}")
            
            # Get the updated data from database
            updated_tax_records = db_manager.get_tax_history(apn)
            updated_sales_records = db_manager.get_sales_history(apn)
            
            # Add all data to the property info
            property_info['tax_history'] = updated_tax_records
            property_info['sales_history'] = updated_sales_records
            property_info['data_completeness'] = {
                'has_tax_data': len(updated_tax_records) > 0,
                'has_sales_data': len(updated_sales_records) > 0,
                'tax_records_count': len(updated_tax_records),
                'sales_records_count': len(updated_sales_records)
            }
            
            logger.info(f"Complete property data compiled for APN {apn}: "
                      f"{len(updated_tax_records)} tax records, {len(updated_sales_records)} sales records")
            
            return property_info
            
        except Exception as e:
            logger.error(f"Error getting complete property data for APN {apn}: {e}")
            return None


class MockMaricopaAPIClient(MaricopaAPIClient):
    """Mock API client for testing and development"""
    
    def __init__(self, config_manager):
        # Initialize parent but don't actually make HTTP requests
        self.config = config_manager.get_api_config()
        self.base_url = self.config['base_url']
        self.token = self.config['token']
        
        logger.info("Initializing Mock API Client")
        logger.warning("Using Mock API Client - no actual API calls will be made")
        logger.debug(f"Mock API Configuration - Base URL: {self.base_url}")
    
    def _generate_mock_property(self, apn: str) -> Dict:
        """Generate mock property data"""
        import random
        
        logger.debug(f"Generating mock property data for APN: {apn}")
        
        return {
            'apn': apn,
            'owner_name': f'Mock Owner {apn[-4:]}',
            'property_address': f'{random.randint(100, 9999)} Mock Street, Phoenix, AZ 8510{random.randint(1, 9)}',
            'mailing_address': f'PO Box {random.randint(1000, 9999)}, Phoenix, AZ 8510{random.randint(1, 9)}',
            'legal_description': f'Mock Legal Description for {apn}',
            'land_use_code': random.choice(['R1', 'R2', 'C1', 'I1']),
            'year_built': random.randint(1950, 2023),
            'living_area_sqft': random.randint(800, 5000),
            'lot_size_sqft': random.randint(5000, 20000),
            'bedrooms': random.randint(2, 6),
            'bathrooms': random.randint(1, 4),
            'pool': random.choice([True, False]),
            'garage_spaces': random.randint(0, 3)
        }
    
    # @perf_logger.log_performance('mock_search_by_apn')
    def search_by_apn(self, apn: str) -> Optional[Dict]:
        """Mock search by APN"""
        logger.info(f"Mock: Searching property by APN: {apn}")
        
        result = self._generate_mock_property(apn)
        logger.info(f"SEARCH_ANALYTICS: mock_apn_search, results=1, apn={apn}")
        
        return result
    
    # @perf_logger.log_performance('mock_search_by_owner')
    def search_by_owner(self, owner_name: str, limit: int = 50) -> List[Dict]:
        """Mock search by owner"""
        logger.info(f"Mock: Searching properties by owner: {owner_name} (limit: {limit})")
        
        result_count = min(3, limit)
        results = [self._generate_mock_property(f"12345{i:03d}") for i in range(result_count)]
        
        logger.info(f"Mock: Generated {result_count} properties for owner: {owner_name}")
        logger.info(f"SEARCH_ANALYTICS: mock_owner_search, results={result_count}, limit={limit}")
        
        return results
    
    # @perf_logger.log_performance('mock_search_by_address')
    def search_by_address(self, address: str, limit: int = 50) -> List[Dict]:
        """Mock search by address"""
        logger.info(f"Mock: Searching properties by address: {address} (limit: {limit})")
        
        result_count = min(2, limit)
        results = [self._generate_mock_property(f"67890{i:03d}") for i in range(result_count)]
        
        logger.info(f"Mock: Generated {result_count} properties for address: {address}")
        logger.info(f"SEARCH_ANALYTICS: mock_address_search, results={result_count}, limit={limit}")
        
        return results
    
    def get_api_status(self) -> Dict[str, Any]:
        """Mock API status"""
        logger.debug("Mock: Getting API status")
        
        return {
            'status': 'mock',
            'version': '1.0.0-mock',
            'rate_limit': {'requests_per_minute': 60},
            'endpoints': ['mock_endpoints']
        }