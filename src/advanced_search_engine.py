"""
Advanced Search Engine with Fuzzy Matching and Geographic Filtering
Phase 6 Advanced Features - Sophisticated search capabilities beyond basic API queries
Provides fuzzy string matching, geographic radius search, and multi-criteria filtering
"""

import re
import math
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from enum import Enum
from pathlib import Path
import json

# For fuzzy string matching
try:
    from difflib import SequenceMatcher
    import unicodedata

    FUZZY_SEARCH_AVAILABLE = True
except ImportError:
    FUZZY_SEARCH_AVAILABLE = False

# For geographic calculations
try:
    import geopy
    from geopy.distance import geodesic
    from geopy.geocoders import Nominatim

    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

from .enhanced_api_client import EnhancedMaricopaAPIClient, EnhancedSearchResult
from .logging_config import get_api_logger

logger = get_api_logger(__name__)


class SearchMode(Enum):
    """Search execution modes"""

    EXACT_MATCH = "exact"
    FUZZY_MATCH = "fuzzy"
    GEOGRAPHIC_RADIUS = "geographic"
    MULTI_CRITERIA = "multi"
    BOOLEAN_QUERY = "boolean"


class SortOrder(Enum):
    """Result sorting options"""

    RELEVANCE = "relevance"
    DISTANCE = "distance"
    ASSESSED_VALUE = "assessed_value"
    DATE_MODIFIED = "date_modified"
    ALPHABETICAL = "alphabetical"


@dataclass
class GeographicPoint:
    """Geographic coordinate point"""

    latitude: float
    longitude: float
    address: Optional[str] = None

    def distance_to(self, other: "GeographicPoint") -> float:
        """Calculate distance in miles to another point"""
        if not GEOPY_AVAILABLE:
            # Fallback to Haversine formula
            return self._haversine_distance(other)

        return geodesic(
            (self.latitude, self.longitude), (other.latitude, other.longitude)
        ).miles

    def _haversine_distance(self, other: "GeographicPoint") -> float:
        """Haversine formula for calculating distance between coordinates"""
        R = 3959  # Earth's radius in miles

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c


@dataclass
class SearchCriteria:
    """Comprehensive search criteria specification"""

    # Basic search
    query: str = ""
    search_mode: SearchMode = SearchMode.FUZZY_MATCH

    # Fuzzy search parameters
    fuzzy_threshold: float = 0.85
    fuzzy_fields: List[str] = field(default_factory=lambda: ["address", "owner", "apn"])

    # Geographic search
    center_point: Optional[GeographicPoint] = None
    radius_miles: float = 1.0

    # Multi-criteria filters
    property_type: Optional[str] = None
    assessed_value_min: Optional[float] = None
    assessed_value_max: Optional[float] = None
    year_built_min: Optional[int] = None
    year_built_max: Optional[int] = None
    square_feet_min: Optional[float] = None
    square_feet_max: Optional[float] = None

    # Date range filters
    sale_date_from: Optional[datetime] = None
    sale_date_to: Optional[datetime] = None
    assessment_date_from: Optional[datetime] = None
    assessment_date_to: Optional[datetime] = None

    # Result options
    sort_by: SortOrder = SortOrder.RELEVANCE
    max_results: int = 100
    include_inactive: bool = False

    # Boolean query
    boolean_query: Optional[str] = None


@dataclass
class SearchResult:
    """Individual search result with relevance scoring"""

    property_data: Dict[str, Any]
    relevance_score: float = 0.0
    distance_miles: Optional[float] = None
    matched_fields: List[str] = field(default_factory=list)
    search_source: str = "unknown"

    def get_display_address(self) -> str:
        """Get formatted address for display"""
        return self.property_data.get("address", "Address not available")

    def get_apn(self) -> str:
        """Get APN for this property"""
        return self.property_data.get("apn", "")

    def get_assessed_value(self) -> float:
        """Get assessed value as float"""
        value_str = self.property_data.get("assessed_value", "0")
        if isinstance(value_str, str):
            # Remove currency symbols and commas
            value_str = re.sub(r"[$,]", "", value_str)
            try:
                return float(value_str)
            except ValueError:
                return 0.0
        return float(value_str) if value_str else 0.0


class FuzzyMatcher:
    """Advanced fuzzy string matching with configurable algorithms"""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.cache = {}
        self.cache_lock = Lock()

    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings"""
        if not str1 or not str2:
            return 0.0

        # Normalize strings
        norm_str1 = self._normalize_string(str1)
        norm_str2 = self._normalize_string(str2)

        # Check cache
        cache_key = (norm_str1, norm_str2)
        with self.cache_lock:
            if cache_key in self.cache:
                return self.cache[cache_key]

        # Calculate multiple similarity metrics
        sequence_ratio = SequenceMatcher(None, norm_str1, norm_str2).ratio()

        # Jaccard similarity for word-based matching
        words1 = set(norm_str1.split())
        words2 = set(norm_str2.split())
        jaccard_similarity = (
            len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0.0
        )

        # Weighted combination
        final_score = (sequence_ratio * 0.7) + (jaccard_similarity * 0.3)

        # Cache result
        with self.cache_lock:
            self.cache[cache_key] = final_score

            # Limit cache size
            if len(self.cache) > 1000:
                # Remove oldest entries
                oldest_keys = list(self.cache.keys())[:100]
                for key in oldest_keys:
                    del self.cache[key]

        return final_score

    def _normalize_string(self, text: str) -> str:
        """Normalize string for comparison"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove accents and special characters
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # Remove extra whitespace and punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def find_best_matches(
        self, query: str, candidates: List[str], max_results: int = 10
    ) -> List[Tuple[str, float]]:
        """Find best matching candidates for a query"""
        scores = []

        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score >= self.threshold:
                scores.append((candidate, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:max_results]


class GeographicCalculator:
    """Geographic calculations and address geocoding"""

    def __init__(self):
        self.geocoder = None

        if GEOPY_AVAILABLE:
            self.geocoder = Nominatim(user_agent="maricopa_property_search")

        # Cache for geocoded addresses
        self.geocode_cache = {}
        self.cache_lock = Lock()

    def geocode_address(self, address: str) -> Optional[GeographicPoint]:
        """Convert address to geographic coordinates"""
        if not address:
            return None

        # Check cache first
        with self.cache_lock:
            if address in self.geocode_cache:
                return self.geocode_cache[address]

        if not self.geocoder:
            logger.warning("Geocoding not available - geopy not installed")
            return None

        try:
            # Add "Maricopa County, AZ" if not present
            search_address = address
            if "arizona" not in address.lower() and "az" not in address.lower():
                search_address += ", Maricopa County, AZ"

            location = self.geocoder.geocode(search_address, timeout=10)

            if location:
                point = GeographicPoint(
                    latitude=location.latitude,
                    longitude=location.longitude,
                    address=address,
                )

                # Cache result
                with self.cache_lock:
                    self.geocode_cache[address] = point

                return point

        except Exception as e:
            logger.warning(f"Geocoding failed for '{address}': {str(e)}")

        return None

    def find_properties_in_radius(
        self,
        center: GeographicPoint,
        radius_miles: float,
        properties: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Find properties within radius of center point"""
        results = []

        for prop in properties:
            prop_address = prop.get("address", "")
            if not prop_address:
                continue

            prop_location = self.geocode_address(prop_address)
            if not prop_location:
                continue

            distance = center.distance_to(prop_location)

            if distance <= radius_miles:
                results.append((prop, distance))

        # Sort by distance
        results.sort(key=lambda x: x[1])

        return results


class AdvancedSearchEngine:
    """
    Advanced search engine with fuzzy matching, geographic filtering, and multi-criteria search
    """

    def __init__(
        self,
        api_client: Optional[EnhancedMaricopaAPIClient] = None,
        database_manager=None,
        fuzzy_threshold: float = 0.85,
    ):

        self.api_client = api_client or EnhancedMaricopaAPIClient()
        self.database_manager = database_manager

        # Initialize search components
        self.fuzzy_matcher = FuzzyMatcher(threshold=fuzzy_threshold)
        self.geo_calculator = GeographicCalculator()

        # Search statistics
        self.search_stats = {
            "total_searches": 0,
            "fuzzy_searches": 0,
            "geographic_searches": 0,
            "multi_criteria_searches": 0,
            "average_results": 0.0,
            "average_search_time": 0.0,
        }

        logger.info("Advanced Search Engine initialized")
        logger.info(f"Fuzzy search available: {FUZZY_SEARCH_AVAILABLE}")
        logger.info(f"Geographic search available: {GEOPY_AVAILABLE}")

    def search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """
        Execute advanced search with specified criteria

        Args:
            criteria: SearchCriteria object with search parameters

        Returns:
            List of SearchResult objects sorted by relevance/distance
        """
        start_time = time.time()
        self.search_stats["total_searches"] += 1

        logger.info(
            f"Executing advanced search: mode={criteria.search_mode.value}, query='{criteria.query}'"
        )

        results = []

        try:
            if criteria.search_mode == SearchMode.EXACT_MATCH:
                results = self._exact_search(criteria)

            elif criteria.search_mode == SearchMode.FUZZY_MATCH:
                results = self._fuzzy_search(criteria)
                self.search_stats["fuzzy_searches"] += 1

            elif criteria.search_mode == SearchMode.GEOGRAPHIC_RADIUS:
                results = self._geographic_search(criteria)
                self.search_stats["geographic_searches"] += 1

            elif criteria.search_mode == SearchMode.MULTI_CRITERIA:
                results = self._multi_criteria_search(criteria)
                self.search_stats["multi_criteria_searches"] += 1

            elif criteria.search_mode == SearchMode.BOOLEAN_QUERY:
                results = self._boolean_search(criteria)

            # Apply post-processing filters
            results = self._apply_filters(results, criteria)

            # Sort results
            results = self._sort_results(results, criteria.sort_by)

            # Limit results
            results = results[: criteria.max_results]

            # Update statistics
            search_time = time.time() - start_time
            result_count = len(results)

            # Update averages
            total_searches = self.search_stats["total_searches"]
            self.search_stats["average_results"] = (
                self.search_stats["average_results"] * (total_searches - 1)
                + result_count
            ) / total_searches
            self.search_stats["average_search_time"] = (
                self.search_stats["average_search_time"] * (total_searches - 1)
                + search_time
            ) / total_searches

            logger.info(
                f"Search completed: {result_count} results in {search_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"Advanced search failed: {str(e)}")
            raise

        return results

    def _exact_search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Perform exact match search"""
        results = []

        # Try different search types
        search_methods = [
            ("apn", self.api_client.search_property_enhanced),
            ("address", self.api_client.search_property_enhanced),
            ("owner", self.api_client.search_property_enhanced),
        ]

        for search_type, search_method in search_methods:
            try:
                api_result = search_method(
                    identifier=criteria.query,
                    search_type=search_type,
                    use_playwright=True,
                )

                if api_result.success:
                    search_result = SearchResult(
                        property_data=api_result.data,
                        relevance_score=1.0,  # Exact match
                        matched_fields=[search_type],
                        search_source="api_exact",
                    )
                    results.append(search_result)
                    break  # Found exact match

            except Exception as e:
                logger.warning(f"Exact search failed for {search_type}: {str(e)}")
                continue

        return results

    def _fuzzy_search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Perform fuzzy string matching search"""
        results = []

        # Get candidate properties from various sources
        candidates = self._get_search_candidates(criteria)

        for candidate in candidates:
            best_score = 0.0
            matched_fields = []

            # Check fuzzy match against specified fields
            for field in criteria.fuzzy_fields:
                field_value = candidate.get(field, "")
                if not field_value:
                    continue

                score = self.fuzzy_matcher.calculate_similarity(
                    criteria.query, str(field_value)
                )

                if score >= criteria.fuzzy_threshold:
                    if score > best_score:
                        best_score = score
                    matched_fields.append(field)

            if best_score >= criteria.fuzzy_threshold:
                search_result = SearchResult(
                    property_data=candidate,
                    relevance_score=best_score,
                    matched_fields=matched_fields,
                    search_source="fuzzy",
                )
                results.append(search_result)

        return results

    def _geographic_search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Perform geographic radius search"""
        results = []

        if not criteria.center_point:
            logger.warning("Geographic search requires center_point")
            return results

        # Get candidate properties
        candidates = self._get_search_candidates(criteria)

        # Find properties within radius
        properties_in_radius = self.geo_calculator.find_properties_in_radius(
            center=criteria.center_point,
            radius_miles=criteria.radius_miles,
            properties=candidates,
        )

        for prop, distance in properties_in_radius:
            search_result = SearchResult(
                property_data=prop,
                relevance_score=max(
                    0.1, 1.0 - (distance / criteria.radius_miles)
                ),  # Distance-based relevance
                distance_miles=distance,
                matched_fields=["location"],
                search_source="geographic",
            )
            results.append(search_result)

        return results

    def _multi_criteria_search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Perform multi-criteria filtered search"""
        results = []

        # Start with a broad search
        candidates = self._get_search_candidates(criteria)

        for candidate in candidates:
            # Apply all criteria filters
            if self._matches_criteria(candidate, criteria):
                # Calculate relevance based on how well it matches criteria
                relevance = self._calculate_multi_criteria_relevance(
                    candidate, criteria
                )

                search_result = SearchResult(
                    property_data=candidate,
                    relevance_score=relevance,
                    matched_fields=["multi_criteria"],
                    search_source="multi_criteria",
                )
                results.append(search_result)

        return results

    def _boolean_search(self, criteria: SearchCriteria) -> List[SearchResult]:
        """Perform boolean query search"""
        # This is a simplified boolean search - could be expanded with proper query parsing
        results = []

        if not criteria.boolean_query:
            return results

        # Parse simple boolean operations (AND, OR, NOT)
        query_parts = self._parse_boolean_query(criteria.boolean_query)

        candidates = self._get_search_candidates(criteria)

        for candidate in candidates:
            if self._evaluate_boolean_query(candidate, query_parts):
                search_result = SearchResult(
                    property_data=candidate,
                    relevance_score=0.8,  # Fixed relevance for boolean matches
                    matched_fields=["boolean"],
                    search_source="boolean",
                )
                results.append(search_result)

        return results

    def _get_search_candidates(self, criteria: SearchCriteria) -> List[Dict[str, Any]]:
        """Get candidate properties for search operations"""
        candidates = []

        # If we have a database manager, query it for candidates
        if self.database_manager:
            try:
                # This would be implemented based on the database schema
                # For now, return empty list
                logger.info("Database search candidates not implemented")
            except Exception as e:
                logger.warning(f"Database candidate search failed: {str(e)}")

        # If query is specific enough, try API search
        if criteria.query and len(criteria.query) > 3:
            try:
                # Try different search approaches
                search_types = ["apn", "address", "owner"]

                for search_type in search_types:
                    api_result = self.api_client.search_property_enhanced(
                        identifier=criteria.query,
                        search_type=search_type,
                        use_playwright=True,
                    )

                    if api_result.success and api_result.data:
                        candidates.append(api_result.data)

            except Exception as e:
                logger.warning(f"API candidate search failed: {str(e)}")

        return candidates

    def _matches_criteria(
        self, property_data: Dict[str, Any], criteria: SearchCriteria
    ) -> bool:
        """Check if property matches search criteria"""

        # Property type filter
        if criteria.property_type:
            prop_type = property_data.get("property_type", "")
            if criteria.property_type.lower() not in prop_type.lower():
                return False

        # Assessed value range
        if criteria.assessed_value_min or criteria.assessed_value_max:
            assessed_value = self._extract_numeric_value(
                property_data.get("assessed_value", "0")
            )

            if (
                criteria.assessed_value_min
                and assessed_value < criteria.assessed_value_min
            ):
                return False

            if (
                criteria.assessed_value_max
                and assessed_value > criteria.assessed_value_max
            ):
                return False

        # Year built range
        if criteria.year_built_min or criteria.year_built_max:
            year_built = self._extract_year(property_data.get("year_built", ""))

            if criteria.year_built_min and year_built < criteria.year_built_min:
                return False

            if criteria.year_built_max and year_built > criteria.year_built_max:
                return False

        # Square feet range
        if criteria.square_feet_min or criteria.square_feet_max:
            sq_ft = self._extract_numeric_value(property_data.get("square_feet", "0"))

            if criteria.square_feet_min and sq_ft < criteria.square_feet_min:
                return False

            if criteria.square_feet_max and sq_ft > criteria.square_feet_max:
                return False

        return True

    def _calculate_multi_criteria_relevance(
        self, property_data: Dict[str, Any], criteria: SearchCriteria
    ) -> float:
        """Calculate relevance score for multi-criteria search"""
        score = 0.0
        factors = 0

        # Query text relevance
        if criteria.query:
            best_field_score = 0.0
            for field in ["address", "owner", "apn", "legal_description"]:
                field_value = property_data.get(field, "")
                if field_value:
                    field_score = self.fuzzy_matcher.calculate_similarity(
                        criteria.query, str(field_value)
                    )
                    best_field_score = max(best_field_score, field_score)

            score += best_field_score
            factors += 1

        # Assessed value preference (higher values get slightly higher scores)
        assessed_value = self._extract_numeric_value(
            property_data.get("assessed_value", "0")
        )
        if assessed_value > 0:
            # Normalize to 0-1 range (assuming max reasonable value of $2M)
            value_score = min(1.0, assessed_value / 2000000)
            score += value_score * 0.3  # Lower weight for value
            factors += 1

        # Recency bonus for recent sales/assessments
        # This would require date parsing from the property data

        return score / factors if factors > 0 else 0.0

    def _parse_boolean_query(self, query: str) -> List[Dict[str, Any]]:
        """Parse boolean query into searchable components"""
        # Simplified boolean parsing - could be enhanced with proper parser
        query_parts = []

        # Split on AND, OR operators
        terms = re.split(r"\s+(AND|OR|NOT)\s+", query, flags=re.IGNORECASE)

        current_op = "AND"
        for term in terms:
            term = term.strip()
            if term.upper() in ["AND", "OR", "NOT"]:
                current_op = term.upper()
            elif term:
                query_parts.append({"term": term, "operator": current_op})

        return query_parts

    def _evaluate_boolean_query(
        self, property_data: Dict[str, Any], query_parts: List[Dict[str, Any]]
    ) -> bool:
        """Evaluate boolean query against property data"""
        if not query_parts:
            return False

        result = True

        for part in query_parts:
            term = part["term"]
            operator = part["operator"]

            # Check if term matches any field in property data
            term_match = False
            for field_value in property_data.values():
                if field_value and term.lower() in str(field_value).lower():
                    term_match = True
                    break

            # Apply boolean operator
            if operator == "AND":
                result = result and term_match
            elif operator == "OR":
                result = result or term_match
            elif operator == "NOT":
                result = result and not term_match

        return result

    def _apply_filters(
        self, results: List[SearchResult], criteria: SearchCriteria
    ) -> List[SearchResult]:
        """Apply additional filters to search results"""
        filtered_results = []

        for result in results:
            # Date range filters
            if criteria.sale_date_from or criteria.sale_date_to:
                # This would require parsing sale dates from property data
                # For now, include all results
                pass

            # Include inactive properties filter
            if not criteria.include_inactive:
                # Filter out inactive properties if we have that information
                status = result.property_data.get("status", "active")
                if status.lower() in ["inactive", "closed", "demolished"]:
                    continue

            filtered_results.append(result)

        return filtered_results

    def _sort_results(
        self, results: List[SearchResult], sort_by: SortOrder
    ) -> List[SearchResult]:
        """Sort search results by specified criteria"""

        if sort_by == SortOrder.RELEVANCE:
            results.sort(key=lambda x: x.relevance_score, reverse=True)

        elif sort_by == SortOrder.DISTANCE and any(
            r.distance_miles is not None for r in results
        ):
            results.sort(
                key=lambda x: (
                    x.distance_miles if x.distance_miles is not None else float("inf")
                )
            )

        elif sort_by == SortOrder.ASSESSED_VALUE:
            results.sort(key=lambda x: x.get_assessed_value(), reverse=True)

        elif sort_by == SortOrder.ALPHABETICAL:
            results.sort(key=lambda x: x.get_display_address().lower())

        elif sort_by == SortOrder.DATE_MODIFIED:
            # Would require date parsing from property data
            # For now, keep current order
            pass

        return results

    def _extract_numeric_value(self, value: Union[str, int, float]) -> float:
        """Extract numeric value from string"""
        if isinstance(value, (int, float)):
            return float(value)

        if not value:
            return 0.0

        # Remove currency symbols, commas, and other non-numeric characters
        numeric_str = re.sub(r"[^\d.]", "", str(value))

        try:
            return float(numeric_str) if numeric_str else 0.0
        except ValueError:
            return 0.0

    def _extract_year(self, value: Union[str, int]) -> int:
        """Extract year from string or return as int"""
        if isinstance(value, int):
            return value

        if not value:
            return 0

        # Extract 4-digit year
        year_match = re.search(r"\b(19|20)\d{2}\b", str(value))
        if year_match:
            return int(year_match.group())

        return 0

    def export_results(
        self, results: List[SearchResult], format: str = "json", filename: str = None
    ) -> str:
        """Export search results to file"""

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.{format.lower()}"

        filepath = Path(filename)

        if format.lower() == "json":
            export_data = []
            for result in results:
                export_data.append(
                    {
                        "property_data": result.property_data,
                        "relevance_score": result.relevance_score,
                        "distance_miles": result.distance_miles,
                        "matched_fields": result.matched_fields,
                        "search_source": result.search_source,
                    }
                )

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

        elif format.lower() == "csv":
            import csv

            with open(filepath, "w", newline="") as f:
                if results:
                    # Get all possible fields
                    all_fields = set()
                    for result in results:
                        all_fields.update(result.property_data.keys())

                    fieldnames = ["relevance_score", "distance_miles"] + sorted(
                        all_fields
                    )

                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for result in results:
                        row = {
                            "relevance_score": result.relevance_score,
                            "distance_miles": result.distance_miles,
                            **result.property_data,
                        }
                        writer.writerow(row)

        logger.info(f"Exported {len(results)} results to {filepath}")
        return str(filepath)

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            **self.search_stats,
            "fuzzy_matcher_cache_size": len(self.fuzzy_matcher.cache),
            "geocode_cache_size": len(self.geo_calculator.geocode_cache),
            "capabilities": {
                "fuzzy_search": FUZZY_SEARCH_AVAILABLE,
                "geographic_search": GEOPY_AVAILABLE,
            },
        }


# Convenience functions for common search operations
def fuzzy_property_search(
    query: str, threshold: float = 0.85, max_results: int = 10
) -> List[SearchResult]:
    """Convenience function for fuzzy property search"""
    engine = AdvancedSearchEngine()

    criteria = SearchCriteria(
        query=query,
        search_mode=SearchMode.FUZZY_MATCH,
        fuzzy_threshold=threshold,
        max_results=max_results,
    )

    return engine.search(criteria)


def geographic_property_search(
    address: str, radius_miles: float = 1.0, max_results: int = 20
) -> List[SearchResult]:
    """Convenience function for geographic property search"""
    engine = AdvancedSearchEngine()

    # Geocode the address
    center_point = engine.geo_calculator.geocode_address(address)

    if not center_point:
        logger.error(f"Could not geocode address: {address}")
        return []

    criteria = SearchCriteria(
        search_mode=SearchMode.GEOGRAPHIC_RADIUS,
        center_point=center_point,
        radius_miles=radius_miles,
        max_results=max_results,
        sort_by=SortOrder.DISTANCE,
    )

    return engine.search(criteria)
