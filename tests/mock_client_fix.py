#!/usr/bin/env python3
"""
Fix for MockMaricopaAPIClient issues found during testing
"""
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# MIGRATED: from api_client import MockMaricopaAPIClient  # → from src.api_client_unified import UnifiedMaricopaAPIClient

class FixedMockMaricopaAPIClient(MockMaricopaAPIClient):
    """Fixed version of MockMaricopaAPIClient with missing methods and attributes"""
    def __init__(self, config_manager):
        super().__init__(config_manager)

        # Add missing attributes that parent class expects
        self.last_request_time = 0
        self.min_request_interval = 0.1
        self.max_retries = 3
        self.timeout = 30

        # Initialize session for compatibility
        self.session = None
    def _rate_limit(self):
        """Mock rate limiting - just track last request time"""
import time

        self.last_request_time = time.time()
    def get_tax_history(self, apn: str, years: int = 5):
        """Mock tax history generation"""
import datetime
import random

        # Generate mock tax records
        tax_records = []
        current_year = datetime.datetime.now().year

        for i in range(years):
            year = current_year - i
            tax_record = {
                'TaxYear': str(year),
                'FullCashValue': random.randint(200000, 800000),
                'LimitedPropertyValue': random.randint(150000, 600000),
                'AssessmentRatioPercentage': random.uniform(8.0, 12.0),
                'TaxAreaCode': f"TA{random.randint(100, 999)}",
                'PEPropUseDesc': random.choice(['Single Family Residential', 'Commercial', 'Multi-Family'])
            }
            tax_records.append(tax_record)

        return tax_records
    def get_sales_history(self, apn: str, years: int = 10):
        """Mock sales history generation"""
import datetime
import random

        # Generate 0-3 mock sales records
        num_sales = random.randint(0, 3)
        sales_records = []

        for i in range(num_sales):
            years_ago = random.randint(1, years)
            sale_date = datetime.datetime.now() - datetime.timedelta(days=years_ago * 365)

            sales_record = {
                'sale_date': sale_date.strftime('%Y-%m-%d'),
                'sale_price': random.randint(150000, 750000),
                'document_type': random.choice(['Warranty Deed', 'Quit Claim Deed', 'Special Warranty Deed']),
                'buyer': f'Mock Buyer {i+1}',
                'seller': f'Mock Seller {i+1}'
            }
            sales_records.append(sales_record)

        return sales_records
    def get_property_details(self, apn: str):
        """Mock property details that calls comprehensive info"""
        return self.get_comprehensive_property_info(apn)
    def get_comprehensive_property_info(self, apn: str):
        """Mock comprehensive property information"""
import random

        # Generate detailed mock property data
        mock_property = self._generate_mock_property(apn)

        # Add comprehensive fields
        mock_property.update({
            'latest_tax_year': '2024',
            'latest_assessed_value': random.randint(200000, 800000),
            'latest_limited_value': random.randint(150000, 600000),
            'assessment_ratio': random.uniform(8.0, 12.0),
            'tax_area_code': f'TA{random.randint(100, 999)}',
            'property_use_description': random.choice(['Single Family Residential', 'Commercial', 'Multi-Family']),
            'quality_grade': random.choice(['A', 'B', 'C', 'D']),
            'exterior_walls': random.choice(['Brick', 'Stucco', 'Wood', 'Vinyl']),
            'roof_type': random.choice(['Tile', 'Shingle', 'Metal', 'Built-up']),
            'parking_details': f'{random.randint(0, 3)} car garage',
            'improvements_count': random.randint(1, 5),
            'total_improvement_sqft': random.randint(800, 5000),
            'detailed_data': {
                'valuations': self.get_tax_history(apn, 5),
                'residential_details': {'mock': 'data'},
                'improvements': [{'mock': 'improvement_data'}],
                'sketches': {'mock': 'sketch_data'},
                'mapids': {'mock': 'map_data'}
            }
        })

        return mock_property
    def get_tax_information(self, apn: str):
        """Mock comprehensive tax information"""
import time

        tax_data = {
            'apn': apn,
            'api_data': self.get_tax_history(apn, 10),
            'scraped_data': None,  # Mock doesn't scrape
            'data_sources': ['mock_api'],
            'timestamp': time.time()
        }

        return tax_data
    def get_property_documents(self, apn: str):
        """Mock property documents"""
import datetime
import random

        # Generate 0-5 mock documents
        num_docs = random.randint(0, 5)
        documents = []

        for i in range(num_docs):
            doc = {
                'document_type': random.choice(['Deed', 'Mortgage', 'Lien', 'Notice', 'Easement']),
                'document_date': (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 3650))).strftime('%Y-%m-%d'),
                'document_number': f'DOC{random.randint(10000, 99999)}',
                'parties': f'Mock Party {i+1}',
                'description': f'Mock document description {i+1}'
            }
            documents.append(doc)

        return documents
    def bulk_property_search(self, apns: list):
        """Mock bulk property search"""
        results = {}

        for apn in apns:
            # Mock has 100% success rate
            results[apn] = self._generate_mock_property(apn)

        return results
    def search_all_property_types(self, query: str, limit: int = 50):
        """Mock search all property types"""
import random

        results = {
            'real_property': [],
            'business_personal_property': [],
            'mobile_home': [],
            'rental': [],
            'subdivisions': []
        }

        # Generate mock results for each category
        for category in results:
            count = random.randint(0, min(5, limit))
            for i in range(count):
                mock_property = self._generate_mock_property(f'{category}{i:03d}')
                mock_property['property_type'] = category.replace('_', ' ').title()
                results[category].append(mock_property)

        return results
    def get_detailed_property_data(self, apn: str):
        """Mock detailed property data"""
        return {
            'valuations': self.get_tax_history(apn, 5),
            'residential_details': {
                'ConstructionYear': 1995,
                'LotSize': 8000,
                'LivableSpace': 1800,
                'Pool': False,
                'ImprovementQualityGrade': 'B',
                'ExteriorWalls': 'Stucco',
                'RoofType': 'Tile',
                'BathFixtures': 2,
                'NumberOfGarages': 2
            },
            'improvements': [{
                'ImprovementDescription': 'Single Family Residence',
                'ImprovementSquareFootage': 1800
            }],
            'sketches': {'mock': 'sketch_data'},
            'mapids': {'mock': 'map_data'}
        }
    def test_fixed_mock_client():
    """Test the fixed mock client"""
    # MIGRATED: from config_manager import ConfigManager  # → from src.enhanced_config_manager import EnhancedConfigManager
        print("Testing Fixed Mock API Client...")

    config_manager = EnhancedConfigManager()
    client = FixedMockMaricopaAPIClient(config_manager)

    test_apn = "12345001"

    # Test all methods that were failing
    try:
        print("Testing get_tax_history...")
        tax_history = client.get_tax_history(test_apn)
        print(f"✅ Tax history: {len(tax_history)} records")
        print("Testing get_sales_history...")
        sales_history = client.get_sales_history(test_apn)
        print(f"✅ Sales history: {len(sales_history)} records")
        print("Testing get_property_details...")
        details = client.get_property_details(test_apn)
        print(f"✅ Property details: {len(details.keys())} fields")
        print("Testing get_comprehensive_property_info...")
        comp_info = client.get_comprehensive_property_info(test_apn)
        print(f"✅ Comprehensive info: {len(comp_info.keys())} fields")
        print("Testing get_tax_information...")
        tax_info = client.get_tax_information(test_apn)
        print(f"✅ Tax information: {tax_info['data_sources']}")
        print("Testing get_property_documents...")
        documents = client.get_property_documents(test_apn)
        print(f"✅ Documents: {len(documents)} records")
        print("Testing bulk_property_search...")
        bulk_results = client.bulk_property_search([test_apn, "12345002"])
        print(f"✅ Bulk search: {len(bulk_results)} properties")
        print("Testing search_all_property_types...")
        all_types = client.search_all_property_types("TEST")
        total_results = sum(len(results) for results in all_types.values())
        print(f"✅ All property types: {total_results} total results")
        print("\n✅ All tests passed! Fixed mock client is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
import traceback

from src.api_client_unified import UnifiedMaricopaAPIClient
from src.enhanced_config_manager import EnhancedConfigManager

        traceback.print_exc()

    if __name__ == "__main__":
    test_fixed_mock_client()