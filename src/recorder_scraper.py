#!/usr/bin/env python
"""
Maricopa County Recorder Document Scraper
Scrapes property document and sales history from recorder.maricopa.gov
"""
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from logging_config import get_logger

logger = get_logger(__name__)


class MaricopaRecorderScraper:
    """Scrape document and sales data from Maricopa County Recorder website using browser automation"""
    def __init__(self):
        logger.info("Initializing Maricopa Recorder Scraper")

        # Recorder URLs from documentation
        self.base_urls = {
            "document_search": "https://recorder.maricopa.gov/recording/document-search.html",
            "parcel_search": "https://recorder.maricopa.gov/recording/parcel-search.html",
            "name_search": "https://recorder.maricopa.gov/recording/name-search.html",
            "address_search": "https://recorder.maricopa.gov/recording/address-search.html",
        }
    def scrape_document_data_for_apn(
        self, apn: str, playwright_page
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape document data for an APN using Playwright page

        Args:
            apn: The APN to search for (e.g., '13304014A')
            playwright_page: Active Playwright page object

        Returns:
            Dictionary containing document information and sales history
        """
        logger.info(f"Scraping recorder data for APN: {apn}")

    try:
            # Start with parcel search
            document_data = self._search_by_parcel(apn, playwright_page)

            if document_data:
                logger.info(f"Successfully scraped recorder data for APN: {apn}")
                return document_data
            else:
                logger.warning(f"No recorder data found for APN: {apn}")
                return None

    except Exception as e:
            logger.error(f"Error scraping recorder data for APN {apn}: {e}")
            return None
    def _search_by_parcel(self, apn: str, page) -> Optional[Dict[str, Any]]:
        """Search for documents by parcel number (APN)"""
    try:
            # Navigate to parcel search page with increased timeout
            page.goto(self.base_urls["parcel_search"], timeout=60000)
            page.wait_for_load_state("networkidle", timeout=30000)

            # Format APN for search (remove dashes, dots)
            clean_apn = apn.replace("-", "").replace(".", "").strip()

            # Fill in the parcel number with multiple attempts
            parcel_filled = False

            # Try common parcel input selectors
            selectors_to_try = [
                'input[name*="parcel"]',
                'input[id*="parcel"]',
                'input[placeholder*="parcel" i]',
                'input[name*="APN"]',
                'input[id*="APN"]',
                'input[type="text"]',
            ]

            for selector in selectors_to_try:
    try:
                    parcel_input = page.locator(selector).first
                    if parcel_input.count() > 0:
                        parcel_input.fill(clean_apn)
                        parcel_filled = True
                        logger.debug(
                            f"Successfully filled parcel input using selector: {selector}"
                        )
                        break
    except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not parcel_filled:
                logger.warning(f"Could not find parcel input field for APN {apn}")
                return None

            # Click search button with multiple attempts
            search_clicked = False
            search_selectors = [
                'input[type="submit"]',
                'button[type="submit"]',
                'button:has-text("Search")',
                'input[value*="Search" i]',
                'button:has-text("SEARCH")',
                ".search-button",
                "#search-btn",
            ]

            for selector in search_selectors:
    try:
                    search_button = page.locator(selector).first
                    if search_button.count() > 0:
                        search_button.click()
                        search_clicked = True
                        logger.debug(
                            f"Successfully clicked search using selector: {selector}"
                        )
                        break
    except Exception as e:
                    logger.debug(f"Search selector {selector} failed: {e}")
                    continue

            if not search_clicked:
                logger.warning(f"Could not find or click search button for APN {apn}")
                return None

            # Wait for results to load with increased timeout
    try:
                page.wait_for_load_state("networkidle", timeout=45000)
    except Exception as e:
                logger.warning(
                    f"Page load timeout for APN {apn}, attempting to extract results anyway: {e}"
                )
                # Continue to try extracting results even if page didn't fully load

            # Wait a bit more for any late-loading content
    try:
                page.wait_for_timeout(2000)  # Wait 2 seconds
    except:
            pass

            # Extract results from the page
            return self._extract_document_results(page, apn)

    except Exception as e:
            logger.error(f"Error in parcel search for APN {apn}: {e}")
            return None
    def _extract_document_results(self, page, apn: str) -> Dict[str, Any]:
        """Extract document results from the search results page"""
    try:
            # Get page content with error handling
    try:
                content = page.content()
    except Exception as e:
                logger.warning(f"Could not get page content for APN {apn}: {e}")
                content = ""

            # Check if we got any content at all
            if not content or len(content) < 100:
                logger.warning(f"Page content appears empty or too short for APN {apn}")
                return self._create_empty_result(apn)

            # Extract document records
            documents = []
    try:
                documents = self._parse_document_table(content)
                logger.debug(f"Parsed {len(documents)} documents for APN {apn}")
    except Exception as e:
                logger.warning(f"Error parsing document table for APN {apn}: {e}")

            # Extract sales history from documents
            sales_history = []
    try:
                if documents:
                    sales_history = self._extract_sales_from_documents(documents)
                    logger.debug(
                        f"Extracted {len(sales_history)} sales records for APN {apn}"
                    )
    except Exception as e:
                logger.warning(f"Error extracting sales history for APN {apn}: {e}")

            # Extract property transfers
            transfers = []
    try:
                if documents:
                    transfers = self._extract_property_transfers(documents)
                    logger.debug(
                        f"Extracted {len(transfers)} transfer records for APN {apn}"
                    )
    except Exception as e:
                logger.warning(
                    f"Error extracting property transfers for APN {apn}: {e}"
                )

            result = {
                "apn": apn,
                "documents": documents,
                "sales_history": sales_history,
                "property_transfers": transfers,
                "scrape_source": "recorder.maricopa.gov",
                "scrape_date": datetime.now().isoformat(),
                "extraction_status": "success" if documents else "no_documents_found",
            }

            logger.info(
                f"Document extraction completed for APN {apn}: {len(documents)} docs, {len(sales_history)} sales, {len(transfers)} transfers"
            )
            return result

    except Exception as e:
            logger.error(f"Error extracting document results for APN {apn}: {e}")
            return self._create_empty_result(apn)
    def _create_empty_result(self, apn: str) -> Dict[str, Any]:
        """Create empty result structure for failed extractions"""
        return {
            "apn": apn,
            "documents": [],
            "sales_history": [],
            "property_transfers": [],
            "scrape_source": "recorder.maricopa.gov",
            "scrape_date": datetime.now().isoformat(),
            "extraction_status": "failed",
        }
    def _parse_document_table(self, content: str) -> List[Dict[str, Any]]:
        """Parse document information from HTML table"""
        documents = []

    try:
            # Look for table rows with document data
            # Common patterns for recorder document tables
            row_patterns = [
                r"<tr[^>]*>.*?(\d{4}-\d{6,8}).*?(\d{1,2}/\d{1,2}/\d{4}).*?([A-Z\s]+).*?([^<\n]*?).*?</tr>",
                r"<tr[^>]*>.*?(\w+\s*\d+).*?(\d{1,2}/\d{1,2}/\d{4}).*?([A-Z\s]+).*?</tr>",
            ]

            for pattern in row_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)

                for match in matches:
                    if len(match) >= 3:
                        document = {
                            "document_number": match[0].strip(),
                            "date": self._parse_date(match[1].strip()),
                            "document_type": match[2].strip(),
                            "description": match[3].strip() if len(match) > 3 else "",
                            "raw_data": match,
                        }

                        # Extract additional details if available
                        if len(match) > 4:
                            document["additional_info"] = match[4].strip()

                        documents.append(document)

                if (
                    documents
                ):  # If we found documents with this pattern, stop trying others
                    break

            # Alternative: Parse using more generic table extraction
            if not documents:
                documents = self._generic_table_parse(content)

    except Exception as e:
            logger.error(f"Error parsing document table: {e}")

        return documents[:50]  # Limit to 50 most recent documents
    def _generic_table_parse(self, content: str) -> List[Dict[str, Any]]:
        """Generic table parsing as fallback"""
        documents = []

    try:
            # Find table data cells and try to extract document info
            td_pattern = r"<td[^>]*>(.*?)</td>"
            table_sections = re.findall(
                r"<table[^>]*>(.*?)</table>", content, re.DOTALL | re.IGNORECASE
            )

            for table in table_sections:
                rows = re.findall(
                    r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.IGNORECASE
                )

                for row in rows[1:]:  # Skip header row
                    cells = re.findall(td_pattern, row, re.DOTALL)

                    if len(cells) >= 3:
                        # Clean cell content
                        clean_cells = [
                            re.sub(r"<[^>]+>", "", cell).strip() for cell in cells
                        ]

                        # Try to identify document info
                        document = {
                            "document_number": clean_cells[0],
                            "date": (
                                self._parse_date(clean_cells[1])
                                if len(clean_cells) > 1
                                else None
                            ),
                            "document_type": (
                                clean_cells[2] if len(clean_cells) > 2 else "UNKNOWN"
                            ),
                            "description": (
                                clean_cells[3] if len(clean_cells) > 3 else ""
                            ),
                            "raw_data": clean_cells,
                        }

                        documents.append(document)

                if documents:  # Found documents in this table
                    break

    except Exception as e:
            logger.error(f"Error in generic table parse: {e}")

        return documents
    def _extract_sales_from_documents(
        self, documents: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Extract sales transactions from document records"""
        sales_history = []

        # Document types that typically indicate sales
        sales_doc_types = [
            "DEED",
            "GRANT DEED",
            "WARRANTY DEED",
            "QUIT CLAIM DEED",
            "SPECIAL WARRANTY DEED",
            "TRUSTEE DEED",
            "SHERIFF DEED",
            "BARGAIN AND SALE DEED",
            "DEED OF TRUST",
        ]

    try:
            for doc in documents:
                doc_type = doc.get("document_type", "").upper()

                # Check if this document represents a sale
                is_sale_doc = any(
                    sale_type in doc_type for sale_type in sales_doc_types
                )

                if is_sale_doc:
                    sale_record = {
                        "sale_date": doc.get("date"),
                        "document_number": doc.get("document_number"),
                        "deed_type": doc.get("document_type"),
                        "document_description": doc.get("description", ""),
                        "sale_price": self._extract_sale_price(
                            doc.get("description", "")
                        ),
                        "seller_name": self._extract_grantor(
                            doc.get("description", "")
                        ),
                        "buyer_name": self._extract_grantee(doc.get("description", "")),
                        "recording_number": doc.get("document_number"),
                    }

                    sales_history.append(sale_record)

    except Exception as e:
            logger.error(f"Error extracting sales from documents: {e}")

        # Sort by date, most recent first
        return sorted(sales_history, key=lambda x: x.get("sale_date", ""), reverse=True)
    def _extract_property_transfers(
        self, documents: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Extract all property transfer documents"""
        transfers = []

        transfer_doc_types = [
            "DEED",
            "TRANSFER",
            "CONVEYANCE",
            "ASSIGNMENT",
            "CERTIFICATE",
            "PATENT",
            "FORECLOSURE",
        ]

    try:
            for doc in documents:
                doc_type = doc.get("document_type", "").upper()

                # Check if this is a transfer document
                is_transfer = any(
                    transfer_type in doc_type for transfer_type in transfer_doc_types
                )

                if is_transfer:
                    transfer = {
                        "transfer_date": doc.get("date"),
                        "document_number": doc.get("document_number"),
                        "transfer_type": doc.get("document_type"),
                        "description": doc.get("description", ""),
                        "grantor": self._extract_grantor(doc.get("description", "")),
                        "grantee": self._extract_grantee(doc.get("description", "")),
                        "consideration": self._extract_sale_price(
                            doc.get("description", "")
                        ),
                    }

                    transfers.append(transfer)

    except Exception as e:
            logger.error(f"Error extracting property transfers: {e}")

        return sorted(transfers, key=lambda x: x.get("transfer_date", ""), reverse=True)
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string into ISO format"""
        if not date_str:
            return None

    try:
            # Try common date formats
            date_formats = [
                "%m/%d/%Y",  # MM/DD/YYYY
                "%m-%d-%Y",  # MM-DD-YYYY
                "%Y-%m-%d",  # YYYY-MM-DD
                "%m/%d/%y",  # MM/DD/YY
                "%m-%d-%y",  # MM-DD-YY
            ]

            date_str = date_str.strip()

            for fmt in date_formats:
    try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
    except ValueError:
                    continue

            # If no format matches, return original
            logger.warning(f"Could not parse date: {date_str}")
            return date_str

    except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return date_str
    def _extract_sale_price(self, description: str) -> Optional[float]:
        """Extract sale price from document description"""
        if not description:
            return None

    try:
            # Look for dollar amounts
            price_patterns = [
                r"\$([0-9,]+\.?\d*)",  # $123,456.00
                r"([0-9,]+\.?\d*)\s*dollars",  # 123456 dollars
                r"consideration[:\s]+\$?([0-9,]+\.?\d*)",  # consideration: $123456
                r"sum[:\s]+\$?([0-9,]+\.?\d*)",  # sum: $123456
            ]

            for pattern in price_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(",", "")
                    return float(price_str)

    except Exception as e:
            logger.debug(f"Error extracting sale price from '{description}': {e}")

        return None
    def _extract_grantor(self, description: str) -> Optional[str]:
        """Extract grantor (seller) name from document description"""
        if not description:
            return None

    try:
            # Look for grantor patterns
            grantor_patterns = [
                r"grantor[:\s]+([^,\n]+)",
                r"from[:\s]+([^,\n\(]+)",
                r"seller[:\s]+([^,\n]+)",
                r"([^,\n]+)\s+to\s+",  # Name TO other name
            ]

            for pattern in grantor_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

    except Exception as e:
            logger.debug(f"Error extracting grantor from '{description}': {e}")

        return None
    def _extract_grantee(self, description: str) -> Optional[str]:
        """Extract grantee (buyer) name from document description"""
        if not description:
            return None

    try:
            # Look for grantee patterns
            grantee_patterns = [
                r"grantee[:\s]+([^,\n]+)",
                r"to[:\s]+([^,\n\(]+)",
                r"buyer[:\s]+([^,\n]+)",
                r"\s+to\s+([^,\n]+)",  # Name to NAME
            ]

            for pattern in grantee_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

    except Exception as e:
            logger.debug(f"Error extracting grantee from '{description}': {e}")

        return None
    def search_documents_by_name(
        self, name: str, playwright_page
    ) -> Optional[Dict[str, Any]]:
        """
        Search for documents by owner/party name

        Args:
            name: Name to search for
            playwright_page: Active Playwright page object

        Returns:
            Dictionary containing document search results
        """
        logger.info(f"Searching recorder documents for name: {name}")

    try:
            # Navigate to name search page
            playwright_page.goto(self.base_urls["name_search"])
            playwright_page.wait_for_load_state("networkidle")

            # Fill in the name field
            name_input = playwright_page.locator(
                'input[name*="name"], input[id*="name"], input[placeholder*="name" i]'
            ).first
            if name_input.count() > 0:
                name_input.fill(name)

            # Click search
            search_button = playwright_page.locator(
                'input[type="submit"], button[type="submit"], button:has-text("Search")'
            ).first
            search_button.click()

            # Wait for results
            playwright_page.wait_for_load_state("networkidle")

            # Extract results
            content = playwright_page.content()
            documents = self._parse_document_table(content)

            return {
                "search_name": name,
                "documents": documents,
                "scrape_source": "recorder.maricopa.gov name search",
                "scrape_date": datetime.now().isoformat(),
            }

    except Exception as e:
            logger.error(f"Error searching documents by name '{name}': {e}")
            return None
    def format_recorder_data_for_database(
        self, recorder_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format scraped recorder data for database storage"""
        if not recorder_data:
            return {}

        formatted = {
            "apn": recorder_data.get("apn"),
            "scrape_date": recorder_data.get("scrape_date"),
            "data_source": "recorder_scrape",
        }

        # Format sales history for database
        if "sales_history" in recorder_data:
            formatted["sales_history_records"] = recorder_data["sales_history"]

        # Format document records
        if "documents" in recorder_data:
            formatted["document_records"] = recorder_data["documents"]

        # Format property transfers
        if "property_transfers" in recorder_data:
            formatted["transfer_records"] = recorder_data["property_transfers"]

        return formatted
