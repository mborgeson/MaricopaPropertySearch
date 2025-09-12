#!/usr/bin/env python
"""
Maricopa County Treasurer Tax Data Scraper
"""

import re
from typing import Dict, List, Optional, Any
from src.logging_config import get_logger

logger = get_logger(__name__)

class MaricopaTaxScraper:
    """Scrape tax data from Maricopa County Treasurer website using browser automation"""
    
    def __init__(self):
        logger.info("Initializing Maricopa Tax Scraper")
    
    def scrape_tax_data_for_apn(self, apn: str, playwright_page) -> Optional[Dict[str, Any]]:
        """
        Scrape comprehensive tax data for an APN using Playwright page
        
        Args:
            apn: The APN to search for (e.g., '13304014A')
            playwright_page: Active Playwright page object
            
        Returns:
            Dictionary containing comprehensive tax information
        """
        logger.info(f"Scraping tax data for APN: {apn}")
        
        try:
            # Navigate to treasurer website
            playwright_page.goto('https://treasurer.maricopa.gov/')
            
            # Parse APN into segments (assuming format like 133-04-014-A)
            apn_parts = self._parse_apn(apn)
            if not apn_parts:
                logger.error(f"Could not parse APN format: {apn}")
                return None
            
            # Fill in parcel number segments with error handling
            try:
                # Try the standard approach first
                playwright_page.get_by_role('textbox', name='Parcel Number Parcel/Account').fill(apn_parts[0])
            except:
                # Fallback to locator approach
                try:
                    playwright_page.locator('input[name*="Parcel"], input[id*="Parcel"]').first.fill(apn_parts[0])
                except:
                    logger.warning(f"Could not fill first parcel segment for APN {apn}")
            
            # Fill remaining segments
            segments = [
                ('#taxPayerParcelInput #txtParcelNumMap', apn_parts[1]),
                ('#taxPayerParcelInput #txtParcelNumItem', apn_parts[2]), 
                ('#taxPayerParcelInput #txtParcelNumSplit', apn_parts[3])
            ]
            
            for selector, value in segments:
                try:
                    playwright_page.locator(selector).fill(value)
                except Exception as e:
                    logger.debug(f"Could not fill segment {selector} with {value}: {e}")
            
            # Click search with fallback options
            search_clicked = False
            search_options = [
                lambda: playwright_page.get_by_text('Search', exact=True).click(),
                lambda: playwright_page.get_by_text('Search').click(),
                lambda: playwright_page.locator('input[type="submit"]').click(),
                lambda: playwright_page.locator('button[type="submit"]').click(),
                lambda: playwright_page.locator('#btnSearch').click()
            ]
            
            for search_method in search_options:
                try:
                    search_method()
                    search_clicked = True
                    break
                except Exception as e:
                    logger.debug(f"Search method failed: {e}")
                    
            if not search_clicked:
                logger.error(f"Could not click search button for APN {apn}")
                return None
            
            # Wait for results page to load
            playwright_page.wait_for_load_state('networkidle')
            
            # Extract data from the page
            tax_data = self._extract_tax_data_from_page(playwright_page)
            
            if tax_data:
                tax_data['apn'] = apn
                logger.info(f"Successfully scraped tax data for APN: {apn}")
                return tax_data
            else:
                logger.warning(f"No tax data found for APN: {apn}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping tax data for APN {apn}: {e}")
            return None
    
    def _parse_apn(self, apn: str) -> Optional[List[str]]:
        """Parse APN into 4 segments for the treasurer website form"""
        # Remove any existing dashes and clean up
        clean_apn = apn.replace('-', '').replace('.', '').strip()
        
        # Try to parse common APN formats
        if len(clean_apn) >= 8:
            # Format: 13304014A -> [133, 04, 014, A]
            return [
                clean_apn[:3],   # First 3 digits
                clean_apn[3:5],  # Next 2 digits  
                clean_apn[5:8],  # Next 3 digits
                clean_apn[8:] if len(clean_apn) > 8 else ''  # Remaining (usually letter)
            ]
        
        logger.error(f"APN format not recognized: {apn}")
        return None
    
    def _extract_tax_data_from_page(self, page) -> Optional[Dict[str, Any]]:
        """Extract tax data from the loaded treasurer page"""
        try:
            # Get page content
            content = page.content()
            
            # Extract owner information
            owner_info = self._extract_owner_info(content)
            
            # Extract current tax due information  
            current_tax = self._extract_current_tax_info(content)
            
            # Extract tax history table
            tax_history = self._extract_tax_history_table(content)
            
            return {
                'owner_info': owner_info,
                'current_tax': current_tax,
                'tax_history': tax_history,
                'scrape_source': 'treasurer.maricopa.gov'
            }
            
        except Exception as e:
            logger.error(f"Error extracting tax data from page: {e}")
            return None
    
    def _extract_owner_info(self, content: str) -> Dict[str, str]:
        """Extract owner name and addresses from page content"""
        owner_info = {}
        
        try:
            # Extract owner name and mailing address
            mailing_pattern = r'Current Mailing Name & Address.*?<generic[^>]*>(.*?)</generic>'
            mailing_match = re.search(mailing_pattern, content, re.DOTALL | re.IGNORECASE)
            if mailing_match:
                mailing_text = mailing_match.group(1)
                lines = [line.strip() for line in mailing_text.split('<text>') if line.strip()]
                if lines:
                    owner_info['owner_name'] = lines[0].replace('</text>', '').strip()
                    if len(lines) > 1:
                        address_parts = [line.replace('</text>', '').strip() for line in lines[1:]]
                        owner_info['mailing_address'] = ', '.join(address_parts)
            
            # Extract property address
            property_pattern = r'Property \(Situs\) Address.*?<generic[^>]*>(.*?)</generic>'
            property_match = re.search(property_pattern, content, re.DOTALL | re.IGNORECASE)
            if property_match:
                property_text = property_match.group(1)
                lines = [line.strip() for line in property_text.split('<text>') if line.strip()]
                address_parts = [line.replace('</text>', '').strip() for line in lines]
                owner_info['property_address'] = ', '.join(address_parts)
                
        except Exception as e:
            logger.error(f"Error extracting owner info: {e}")
        
        return owner_info
    
    def _extract_current_tax_info(self, content: str) -> Dict[str, Any]:
        """Extract current year tax information"""
        current_tax = {}
        
        try:
            # Extract assessed tax amount
            assessed_pattern = r'"Assessed Tax:".*?<generic[^>]*>[\s]*\$?([\d,]+\.?\d*)'
            assessed_match = re.search(assessed_pattern, content, re.IGNORECASE)
            if assessed_match:
                current_tax['assessed_tax'] = float(assessed_match.group(1).replace(',', ''))
            
            # Extract tax paid amount
            paid_pattern = r'"Tax Paid:".*?<generic[^>]*>[\s]*\$?([\d,]+\.?\d*)'
            paid_match = re.search(paid_pattern, content, re.IGNORECASE)
            if paid_match:
                current_tax['tax_paid'] = float(paid_match.group(1).replace(',', ''))
            
            # Extract total due
            due_pattern = r'"Total Due:".*?<[^>]*>[\s]*\$?([\d,]+\.?\d*)'
            due_match = re.search(due_pattern, content, re.IGNORECASE)
            if due_match:
                current_tax['total_due'] = float(due_match.group(1).replace(',', ''))
                
            # Determine payment status
            if current_tax.get('total_due', 0) > 0:
                current_tax['payment_status'] = 'UNPAID'
            else:
                current_tax['payment_status'] = 'PAID'
                
        except Exception as e:
            logger.error(f"Error extracting current tax info: {e}")
            
        return current_tax
    
    def _extract_tax_history_table(self, content: str) -> List[Dict[str, Any]]:
        """Extract historical tax data from the tax years table"""
        tax_history = []
        
        try:
            # Find tax years table rows
            row_pattern = r'<row[^>]*>.*?(\d{4}).*?(Paid|Unpaid).*?\$([\d,]+\.?\d*).*?\$([\d,]+\.?\d*).*?</row>'
            rows = re.findall(row_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for row in rows:
                tax_year, status, assessed_tax, amount_due = row
                tax_history.append({
                    'tax_year': int(tax_year),
                    'payment_status': status.upper(),
                    'assessed_tax': float(assessed_tax.replace(',', '')),
                    'amount_due': float(amount_due.replace(',', '')),
                    'tax_paid': float(assessed_tax.replace(',', '')) if status.upper() == 'PAID' else 0.0
                })
                
        except Exception as e:
            logger.error(f"Error extracting tax history: {e}")
        
        return sorted(tax_history, key=lambda x: x['tax_year'], reverse=True)
    
    def format_tax_data_for_database(self, tax_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format scraped tax data for database storage"""
        if not tax_data:
            return {}
        
        formatted = {
            'apn': tax_data.get('apn'),
            'scrape_date': None,  # Will be set by database
            'data_source': 'treasurer_scrape'
        }
        
        # Add owner information
        if 'owner_info' in tax_data:
            owner = tax_data['owner_info']
            formatted.update({
                'owner_name': owner.get('owner_name'),
                'property_address': owner.get('property_address'), 
                'mailing_address': owner.get('mailing_address')
            })
        
        # Add current tax information
        if 'current_tax' in tax_data:
            current = tax_data['current_tax']
            formatted.update({
                'current_tax_amount': current.get('assessed_tax'),
                'current_payment_status': current.get('payment_status'),
                'current_amount_due': current.get('total_due')
            })
            
        # Format tax history for database
        if 'tax_history' in tax_data:
            formatted['tax_history_records'] = tax_data['tax_history']
        
        return formatted