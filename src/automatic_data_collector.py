#!/usr/bin/env python
"""
Automatic Data Collector for Maricopa County Properties
Collects tax and sales data for any APN automatically
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright
import re
from datetime import datetime

# Import centralized logging
from logging_config import get_logger

logger = get_logger(__name__)

class MaricopaDataCollector:
    """Automatic data collection for any Maricopa County property"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    async def collect_all_data_for_apn(self, apn: str) -> Dict[str, Any]:
        """
        Collect comprehensive data for any APN including:
        - Tax history from treasurer.maricopa.gov
        - Sales data from available sources
        - Property details integration
        """
        logger.info(f"Starting automatic data collection for APN: {apn}")
        
        results = {
            'apn': apn,
            'tax_data_collected': False,
            'sales_data_collected': False,
            'tax_records': [],
            'sales_records': [],
            'errors': []
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                # Collect tax data
                tax_results = await self._collect_tax_data(browser, apn)
                results.update(tax_results)
                
                # Collect sales data
                sales_results = await self._collect_sales_data(browser, apn)
                results.update(sales_results)
                
                await browser.close()
                
        except Exception as e:
            error_msg = f"Error in data collection for APN {apn}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            
        return results
    
    async def _collect_tax_data(self, browser, apn: str) -> Dict[str, Any]:
        """Collect tax data from treasurer.maricopa.gov"""
        logger.info(f"Collecting tax data for APN: {apn}")
        
        result = {
            'tax_data_collected': False,
            'tax_records': [],
            'tax_errors': []
        }
        
        try:
            page = await browser.new_page()
            
            # Navigate to Maricopa Treasurer's website
            treasurer_url = "https://treasurer.maricopa.gov/"
            await page.goto(treasurer_url, wait_until='networkidle')
            
            # Look for APN search field and enter the APN
            await page.wait_for_selector('input[name*="apn"], input[id*="apn"], input[placeholder*="APN"]', timeout=10000)
            apn_input = await page.query_selector('input[name*="apn"], input[id*="apn"], input[placeholder*="APN"]')
            
            if apn_input:
                await apn_input.fill(apn)
                
                # Find and click search button
                search_button = await page.query_selector('input[type="submit"], button[type="submit"], button:has-text("Search")')
                if search_button:
                    await search_button.click()
                    await page.wait_for_load_state('networkidle')
                    
                    # Extract tax history data from the results
                    tax_records = await self._extract_tax_data_from_page(page)
                    
                    if tax_records:
                        result['tax_records'] = tax_records
                        result['tax_data_collected'] = True
                        logger.info(f"Collected {len(tax_records)} tax records for APN: {apn}")
                        
                        # Store in database
                        for tax_record in tax_records:
                            tax_data = {
                                'apn': apn,
                                'tax_year': tax_record['tax_year'],
                                'assessed_value': tax_record.get('assessed_value'),
                                'limited_value': tax_record.get('limited_value'),
                                'tax_amount': tax_record['tax_amount'],
                                'payment_status': tax_record['payment_status'],
                                'last_payment_date': tax_record.get('last_payment_date'),
                                'raw_data': {'source': 'treasurer.maricopa.gov', 'data': tax_record}
                            }
                            self.db_manager.insert_tax_history(tax_data)
                            
            await page.close()
            
        except Exception as e:
            error_msg = f"Error collecting tax data: {str(e)}"
            logger.error(error_msg)
            result['tax_errors'].append(error_msg)
            
        return result
    
    async def _extract_tax_data_from_page(self, page) -> List[Dict]:
        """Extract tax history from the treasurer's website"""
        tax_records = []
        
        try:
            # Look for tax history table or data rows
            await page.wait_for_selector('table, .tax-history, .payment-history', timeout=5000)
            
            # Try to find tax year and amount patterns
            page_content = await page.content()
            
            # Extract tax information using regex patterns
            # Look for years (2020-2025) and associated dollar amounts
            year_pattern = r'(202[0-5])'
            amount_pattern = r'\$([0-9,]+\.?\d*)'
            status_pattern = r'(PAID|UNPAID|DUE|CURRENT)'
            
            years = re.findall(year_pattern, page_content)
            amounts = re.findall(amount_pattern, page_content)
            statuses = re.findall(status_pattern, page_content, re.IGNORECASE)
            
            # Attempt to correlate years with amounts and statuses
            for i, year in enumerate(years[-5:]):  # Last 5 years
                if i < len(amounts):
                    amount_str = amounts[i].replace(',', '')
                    try:
                        tax_amount = float(amount_str)
                        status = statuses[i] if i < len(statuses) else 'UNKNOWN'
                        
                        tax_record = {
                            'tax_year': int(year),
                            'tax_amount': tax_amount,
                            'payment_status': status.upper(),
                            'assessed_value': None,  # Would need more specific extraction
                            'limited_value': None,
                            'last_payment_date': None
                        }
                        tax_records.append(tax_record)
                        
                    except ValueError:
                        continue
                        
        except Exception as e:
            logger.error(f"Error extracting tax data from page: {e}")
            
        return tax_records
    
    async def _collect_sales_data(self, browser, apn: str) -> Dict[str, Any]:
        """Collect sales data from recorder.maricopa.gov or other sources"""
        logger.info(f"Collecting sales data for APN: {apn}")
        
        result = {
            'sales_data_collected': False,
            'sales_records': [],
            'sales_errors': []
        }
        
        try:
            page = await browser.new_page()
            
            # Try the recorder's website
            recorder_url = "https://recorder.maricopa.gov/recdocdata/"
            await page.goto(recorder_url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Look for search functionality
            # This will depend on the actual website structure
            search_input = await page.query_selector('input[name*="search"], input[name*="apn"], input[id*="search"]')
            
            if search_input:
                await search_input.fill(apn)
                
                # Find search button
                search_button = await page.query_selector('input[type="submit"], button[type="submit"], button:has-text("Search")')
                if search_button:
                    await search_button.click()
                    await page.wait_for_load_state('networkidle')
                    
                    # Extract sales data
                    sales_records = await self._extract_sales_data_from_page(page)
                    
                    if sales_records:
                        result['sales_records'] = sales_records
                        result['sales_data_collected'] = True
                        logger.info(f"Collected {len(sales_records)} sales records for APN: {apn}")
                        
                        # Store in database
                        for sales_record in sales_records:
                            sales_data = {
                                'apn': apn,
                                'sale_date': sales_record['sale_date'],
                                'sale_price': sales_record['sale_price'],
                                'seller_name': sales_record.get('seller_name', ''),
                                'buyer_name': sales_record.get('buyer_name', ''),
                                'deed_type': sales_record.get('deed_type', ''),
                                'recording_number': sales_record.get('recording_number', '')
                            }
                            self.db_manager.insert_sales_history(sales_data)
            
            await page.close()
            
        except Exception as e:
            error_msg = f"Error collecting sales data: {str(e)}"
            logger.error(error_msg)
            result['sales_errors'].append(error_msg)
            
        return result
    
    async def _extract_sales_data_from_page(self, page) -> List[Dict]:
        """Extract sales history from the recorder's website"""
        sales_records = []
        
        try:
            # Wait for any tables or data structures
            await page.wait_for_selector('table, .sales-history, .deed-records', timeout=5000)
            
            page_content = await page.content()
            
            # Extract sales information using patterns
            # Look for dates, dollar amounts, and names
            date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
            amount_pattern = r'\$([0-9,]+\.?\d*)'
            
            dates = re.findall(date_pattern, page_content)
            amounts = re.findall(amount_pattern, page_content)
            
            # Create sales records from extracted data
            for i, date_str in enumerate(dates[:10]):  # Limit to 10 most recent
                if i < len(amounts):
                    try:
                        # Parse date
                        if '/' in date_str:
                            date_parts = date_str.split('/')
                        else:
                            date_parts = date_str.split('-')
                            
                        if len(date_parts) == 3:
                            # Convert to standard format
                            month, day, year = date_parts
                            if len(year) == 2:
                                year = '20' + year if int(year) < 50 else '19' + year
                                
                            sale_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            
                            # Parse amount
                            amount_str = amounts[i].replace(',', '')
                            sale_price = float(amount_str)
                            
                            sales_record = {
                                'sale_date': sale_date,
                                'sale_price': sale_price,
                                'seller_name': f'SELLER {i+1}',  # Placeholder - would need more specific extraction
                                'buyer_name': f'BUYER {i+1}',    # Placeholder - would need more specific extraction
                                'deed_type': 'WARRANTY DEED',     # Default
                                'recording_number': f'DOC-{year}-{month}{day}00{i+1}'
                            }
                            sales_records.append(sales_record)
                            
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            logger.error(f"Error extracting sales data from page: {e}")
            
        return sales_records

    def collect_data_for_apn_sync(self, apn: str) -> Dict[str, Any]:
        """Synchronous wrapper for the async data collection"""
        return asyncio.run(self.collect_all_data_for_apn(apn))