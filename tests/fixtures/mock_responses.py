"""
Mock responses and test data fixtures for comprehensive testing
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class MockDataGenerator:
    """Generate realistic mock data for testing"""
    
    def __init__(self):
        self.owner_names = [
            "SMITH, JOHN & MARY",
            "JONES, ROBERT M",
            "WILLIAMS, SARAH E",
            "BROWN, MICHAEL J",
            "DAVIS, JENNIFER L",
            "MILLER, DAVID & LISA",
            "WILSON, CHRISTOPHER",
            "MOORE, AMANDA K",
            "TAYLOR, JAMES R",
            "ANDERSON, LINDA M"
        ]
        
        self.street_names = [
            "MAIN ST", "OAK AVE", "PINE ST", "MAPLE DR", "ELM WAY",
            "CEDAR LN", "FIRST AVE", "SECOND ST", "THIRD ST", "PARK BLVD",
            "SUNSET DR", "SUNRISE AVE", "DESERT VIEW RD", "MOUNTAIN RD",
            "VALLEY DR", "RIDGE WAY", "MESA AVE", "CANYON ST"
        ]
        
        self.cities = [
            "PHOENIX", "SCOTTSDALE", "TEMPE", "MESA", "GLENDALE",
            "PEORIA", "SURPRISE", "GOODYEAR", "AVONDALE", "CHANDLER"
        ]
        
        self.property_types = [
            "RESIDENTIAL", "COMMERCIAL", "VACANT LAND", "CONDOMINIUM",
            "TOWNHOUSE", "MOBILE HOME", "INDUSTRIAL"
        ]
        
    def generate_property_data(self, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic property data"""
        properties = []
        
        for i in range(count):
            property_data = {
                'apn': self._generate_apn(i),
                'owner_name': random.choice(self.owner_names),
                'property_address': self._generate_address(i),
                'city': random.choice(self.cities),
                'zip_code': self._generate_zip_code(),
                'property_type': random.choice(self.property_types),
                'assessed_value': self._generate_assessed_value(),
                'market_value': None,
                'square_feet': self._generate_square_feet(),
                'year_built': self._generate_year_built(),
                'bedrooms': self._generate_bedrooms(),
                'bathrooms': self._generate_bathrooms(),
                'lot_size': self._generate_lot_size(),
                'last_updated': datetime.now().isoformat()
            }
            
            # Calculate market value based on assessed value
            property_data['market_value'] = int(property_data['assessed_value'] * random.uniform(1.05, 1.25))
            
            properties.append(property_data)
            
        return properties
        
    def generate_tax_history(self, apn: str, years: int = 5) -> List[Dict[str, Any]]:
        """Generate tax history data"""
        current_year = datetime.now().year
        tax_history = []
        
        base_tax = random.uniform(2000, 8000)
        
        for year_offset in range(years):
            year = current_year - year_offset
            tax_amount = base_tax * (1 + random.uniform(-0.1, 0.15)) ** year_offset
            
            tax_record = {
                'apn': apn,
                'tax_year': year,
                'assessed_value': int(tax_amount * random.uniform(40, 60)),
                'tax_amount': round(tax_amount, 2),
                'paid_date': self._generate_date_in_year(year),
                'delinquent': random.random() < 0.05  # 5% chance of delinquency
            }
            
            tax_history.append(tax_record)
            
        return tax_history
        
    def generate_sales_history(self, apn: str, sales_count: int = None) -> List[Dict[str, Any]]:
        """Generate sales history data"""
        if sales_count is None:
            sales_count = random.choices([0, 1, 2, 3], weights=[30, 50, 15, 5])[0]
            
        sales_history = []
        
        base_price = random.uniform(150000, 600000)
        sale_dates = []
        
        # Generate sale dates going back in time
        for i in range(sales_count):
            years_back = random.uniform(1, 20)
            sale_date = datetime.now() - timedelta(days=365 * years_back)
            sale_dates.append(sale_date)
            
        sale_dates.sort(reverse=True)  # Most recent first
        
        for i, sale_date in enumerate(sale_dates):
            # Earlier sales should generally be cheaper
            appreciation_factor = 1 + (len(sale_dates) - i - 1) * random.uniform(0.03, 0.08)
            sale_price = base_price / appreciation_factor
            
            sale_record = {
                'apn': apn,
                'sale_date': sale_date.strftime('%Y-%m-%d'),
                'sale_price': int(sale_price),
                'buyer': self._generate_buyer_name(),
                'seller': self._generate_seller_name(),
                'document_number': f"DOC{random.randint(100000, 999999)}"
            }
            
            sales_history.append(sale_record)
            
        return sales_history
        
    def generate_api_responses(self) -> Dict[str, Any]:
        """Generate complete API response scenarios"""
        return {
            'successful_search': {
                'status': 'success',
                'results': self.generate_property_data(5),
                'total_count': 5,
                'query_time': random.uniform(0.1, 0.5)
            },
            'empty_search': {
                'status': 'success',
                'results': [],
                'total_count': 0,
                'query_time': random.uniform(0.05, 0.2)
            },
            'large_result_set': {
                'status': 'success',
                'results': self.generate_property_data(100),
                'total_count': 247,  # Indicates more results available
                'query_time': random.uniform(0.3, 1.2)
            },
            'timeout_error': {
                'error': 'timeout',
                'message': 'Request timed out after 30 seconds',
                'status': 'error'
            },
            'server_error': {
                'error': 'server_error',
                'message': 'Internal server error',
                'status': 'error',
                'error_code': 500
            },
            'rate_limited': {
                'error': 'rate_limited',
                'message': 'Rate limit exceeded, try again later',
                'status': 'error',
                'retry_after': 60
            },
            'partial_data': {
                'status': 'partial_success',
                'results': self.generate_property_data(3),
                'total_count': 3,
                'warnings': ['Some data sources unavailable'],
                'query_time': random.uniform(0.2, 0.8)
            }
        }
        
    def generate_scraper_responses(self) -> Dict[str, Any]:
        """Generate web scraper response scenarios"""
        return {
            'successful_scrape': {
                'success': True,
                'data': {
                    'property_details': self.generate_property_data(1)[0],
                    'additional_info': {
                        'zoning': random.choice(['R1-6', 'R2-4', 'C1', 'C2', 'I1']),
                        'school_district': random.choice(['Phoenix Union', 'Scottsdale Unified', 'Tempe Elementary']),
                        'hoa_fees': random.choice([None, 45, 125, 275, 450])
                    }
                },
                'scrape_time': random.uniform(1.0, 5.0)
            },
            'blocked_scrape': {
                'success': False,
                'error': 'blocked',
                'message': 'Request blocked by anti-bot protection',
                'retry_possible': True
            },
            'timeout_scrape': {
                'success': False,
                'error': 'timeout',
                'message': 'Page load timeout after 30 seconds',
                'retry_possible': True
            },
            'not_found_scrape': {
                'success': False,
                'error': 'not_found',
                'message': 'Property not found on county website',
                'retry_possible': False
            },
            'malformed_data': {
                'success': True,
                'data': {
                    'property_details': {
                        'apn': '???-??-???',  # Malformed APN
                        'owner_name': '',
                        'assessed_value': 'N/A',
                        'square_feet': None
                    }
                },
                'warnings': ['Data format inconsistent']
            }
        }
        
    def _generate_apn(self, index: int) -> str:
        """Generate realistic APN (Assessor Parcel Number)"""
        book = random.randint(100, 999)
        map_num = random.randint(10, 99)
        parcel = f"{index:03d}"
        suffix = random.choice(['A', 'B', 'C', 'D', ''])
        return f"{book}-{map_num}-{parcel}{suffix}"
        
    def _generate_address(self, index: int) -> str:
        """Generate realistic property address"""
        house_number = random.randint(100, 9999)
        street_name = random.choice(self.street_names)
        unit = random.choice(['', f' #{random.randint(1, 50)}', f' APT {random.choice("ABCD")}'])
        return f"{house_number} {street_name}{unit}"
        
    def _generate_zip_code(self) -> str:
        """Generate realistic Arizona zip code"""
        return random.choice([
            '85001', '85003', '85004', '85006', '85007', '85008', '85009',
            '85251', '85254', '85258', '85260', '85281', '85282', '85283'
        ])
        
    def _generate_assessed_value(self) -> int:
        """Generate realistic assessed value"""
        property_type = random.choice(self.property_types)
        
        if property_type == 'COMMERCIAL':
            return random.randint(300000, 2000000)
        elif property_type == 'VACANT LAND':
            return random.randint(25000, 150000)
        else:  # Residential types
            return random.randint(150000, 800000)
            
    def _generate_square_feet(self) -> Optional[int]:
        """Generate realistic square footage"""
        if random.random() < 0.05:  # 5% chance of missing data
            return None
        return random.randint(800, 4500)
        
    def _generate_year_built(self) -> Optional[int]:
        """Generate realistic year built"""
        if random.random() < 0.03:  # 3% chance of missing data
            return None
        return random.randint(1950, 2023)
        
    def _generate_bedrooms(self) -> Optional[int]:
        """Generate realistic bedroom count"""
        if random.random() < 0.1:  # 10% chance of missing data
            return None
        return random.choices([1, 2, 3, 4, 5, 6], weights=[5, 15, 35, 30, 10, 5])[0]
        
    def _generate_bathrooms(self) -> Optional[float]:
        """Generate realistic bathroom count"""
        if random.random() < 0.1:  # 10% chance of missing data
            return None
        return random.choices([1, 1.5, 2, 2.5, 3, 3.5, 4], weights=[10, 15, 30, 20, 15, 7, 3])[0]
        
    def _generate_lot_size(self) -> Optional[float]:
        """Generate realistic lot size in acres"""
        if random.random() < 0.15:  # 15% chance of missing data
            return None
        return round(random.uniform(0.15, 2.5), 2)
        
    def _generate_date_in_year(self, year: int) -> str:
        """Generate random date within a year"""
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        return random_date.strftime('%Y-%m-%d')
        
    def _generate_buyer_name(self) -> str:
        """Generate buyer name for sales history"""
        return random.choice(self.owner_names)
        
    def _generate_seller_name(self) -> str:
        """Generate seller name for sales history"""
        return random.choice(self.owner_names)

class MockResponseProvider:
    """Provides mock responses for different testing scenarios"""
    
    def __init__(self):
        self.generator = MockDataGenerator()
        self.response_cache = {}
        
    def get_search_response(self, scenario: str, **kwargs) -> Dict[str, Any]:
        """Get mock response for search scenarios"""
        
        if scenario not in self.response_cache:
            self.response_cache[scenario] = self._generate_scenario_response(scenario, **kwargs)
            
        return self.response_cache[scenario]
        
    def get_property_details_response(self, apn: str, scenario: str = 'normal') -> Dict[str, Any]:
        """Get mock response for property details"""
        
        cache_key = f"details_{apn}_{scenario}"
        
        if cache_key not in self.response_cache:
            if scenario == 'not_found':
                response = {
                    'status': 'not_found',
                    'message': f'Property {apn} not found'
                }
            elif scenario == 'incomplete_data':
                property_data = self.generator.generate_property_data(1)[0]
                property_data['apn'] = apn
                # Remove some fields to simulate incomplete data
                incomplete_fields = ['square_feet', 'year_built', 'bedrooms']
                for field in incomplete_fields:
                    if random.random() < 0.5:
                        property_data[field] = None
                        
                response = {
                    'status': 'success',
                    'property': property_data,
                    'warnings': ['Some property details unavailable']
                }
            else:  # normal scenario
                property_data = self.generator.generate_property_data(1)[0]
                property_data['apn'] = apn
                
                response = {
                    'status': 'success',
                    'property': property_data,
                    'tax_history': self.generator.generate_tax_history(apn),
                    'sales_history': self.generator.generate_sales_history(apn)
                }
                
            self.response_cache[cache_key] = response
            
        return self.response_cache[cache_key]
        
    def _generate_scenario_response(self, scenario: str, **kwargs) -> Dict[str, Any]:
        """Generate response for specific test scenario"""
        
        search_term = kwargs.get('search_term', 'SMITH')
        search_type = kwargs.get('search_type', 'owner')
        
        if scenario == 'successful_search':
            count = kwargs.get('result_count', 5)
            properties = self.generator.generate_property_data(count)
            
            # Customize properties to match search term
            for prop in properties:
                if search_type == 'owner':
                    prop['owner_name'] = f"{search_term}, {random.choice(['JOHN', 'MARY', 'ROBERT', 'LISA'])}"
                elif search_type == 'address':
                    prop['property_address'] = f"{random.randint(100, 9999)} {search_term}"
                elif search_type == 'apn':
                    if count == 1:
                        prop['apn'] = search_term
                        
            return {
                'status': 'success',
                'results': properties,
                'total_count': len(properties),
                'search_term': search_term,
                'search_type': search_type
            }
            
        elif scenario == 'empty_results':
            return {
                'status': 'success',
                'results': [],
                'total_count': 0,
                'search_term': search_term,
                'search_type': search_type
            }
            
        elif scenario == 'api_timeout':
            return {
                'status': 'error',
                'error': 'timeout',
                'message': 'API request timed out',
                'search_term': search_term
            }
            
        elif scenario == 'network_error':
            return {
                'status': 'error',
                'error': 'network',
                'message': 'Network connection failed',
                'search_term': search_term
            }
            
        elif scenario == 'server_error':
            return {
                'status': 'error',
                'error': 'server',
                'message': 'Internal server error',
                'error_code': 500,
                'search_term': search_term
            }
            
        elif scenario == 'rate_limited':
            return {
                'status': 'error',
                'error': 'rate_limit',
                'message': 'Too many requests',
                'retry_after': 60,
                'search_term': search_term
            }
            
        elif scenario == 'partial_success':
            properties = self.generator.generate_property_data(3)
            return {
                'status': 'partial_success',
                'results': properties,
                'total_count': len(properties),
                'warnings': ['Some data sources unavailable'],
                'search_term': search_term
            }
            
        else:
            return self._generate_scenario_response('successful_search', **kwargs)

# Global instance for easy access
mock_provider = MockResponseProvider()

# Convenience functions
def get_mock_properties(count: int = 5) -> List[Dict[str, Any]]:
    """Get mock property data"""
    generator = MockDataGenerator()
    return generator.generate_property_data(count)

def get_mock_search_response(scenario: str = 'successful_search', **kwargs) -> Dict[str, Any]:
    """Get mock search response"""
    return mock_provider.get_search_response(scenario, **kwargs)

def get_mock_property_details(apn: str, scenario: str = 'normal') -> Dict[str, Any]:
    """Get mock property details"""
    return mock_provider.get_property_details_response(apn, scenario)

# Export key components
__all__ = [
    'MockDataGenerator',
    'MockResponseProvider', 
    'mock_provider',
    'get_mock_properties',
    'get_mock_search_response',
    'get_mock_property_details'
]