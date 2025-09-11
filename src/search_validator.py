"""
Search Input Validation and Sanitization
Comprehensive validation for search inputs with security protection
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SearchType(Enum):
    """Supported search types"""
    OWNER = "owner"
    ADDRESS = "address"  
    APN = "apn"

@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: str
    errors: List[str]
    warnings: List[str]
    search_type: Optional[SearchType] = None

class SearchValidator:
    """Input validation and sanitization for property searches"""
    
    def __init__(self):
        # APN patterns for Maricopa County
        self.apn_patterns = [
            r'^\d{3}-\d{2}-\d{3}[A-Z]?$',  # 123-45-678A
            r'^\d{3}-\d{2}-\d{4}$',        # 123-45-6789
            r'^\d{10,11}$',                # 1234567890
            r'^\d{3}\d{2}\d{3,4}[A-Z]?$'   # 12345678A
        ]
        
        # Dangerous SQL injection patterns
        self.sql_injection_patterns = [
            r"('[^']*')|(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|EXECUTE)\b)",
            r"(\b(OR|AND)\b\s+[\w'\"]+\s*=\s*[\w'\"]+)",
            r"(--|#|/\*|\*/)",
            r"(\bWHERE\b\s+[\w'\"]+\s*=\s*[\w'\"]+)",
            r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP))",
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
        ]
        
        # Common name patterns
        self.name_patterns = [
            r"^[A-Za-z\s\.\-']{2,100}$",  # Basic name with common chars
            r"^[A-Za-z][A-Za-z\s\.\-',&]{1,99}$",  # Name starting with letter
        ]
        
        # Address patterns  
        self.address_patterns = [
            r"^\d+\s+[A-Za-z\s\.\-#]+\s+(ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|PL|PLACE|WAY|CIR|CIRCLE)",
            r"^\d+[A-Z]?\s+[A-Za-z\s\.\-#]+",  # More flexible pattern
        ]
    
    def validate_search_input(self, search_term: str, search_type: SearchType) -> ValidationResult:
        """Validate and sanitize search input"""
        errors = []
        warnings = []
        
        # Basic input checks
        if not search_term or not search_term.strip():
            return ValidationResult(False, "", ["Search term cannot be empty"], [])
        
        original_input = search_term
        sanitized_input = self._sanitize_input(search_term)
        
        # Check for security threats
        security_errors = self._check_security_threats(sanitized_input)
        if security_errors:
            return ValidationResult(False, "", security_errors, [])
        
        # Type-specific validation
        if search_type == SearchType.APN:
            is_valid, type_errors, type_warnings = self._validate_apn(sanitized_input)
        elif search_type == SearchType.OWNER:
            is_valid, type_errors, type_warnings = self._validate_owner_name(sanitized_input)
        elif search_type == SearchType.ADDRESS:
            is_valid, type_errors, type_warnings = self._validate_address(sanitized_input)
        else:
            return ValidationResult(False, "", ["Invalid search type"], [])
        
        errors.extend(type_errors)
        warnings.extend(type_warnings)
        
        # Additional sanitization if warnings exist
        if warnings and is_valid:
            sanitized_input = self._advanced_sanitization(sanitized_input, search_type)
        
        # Log validation result
        if not is_valid:
            logger.warning(f"Validation failed for {search_type.value}: {original_input} -> {errors}")
        elif warnings:
            logger.info(f"Validation warnings for {search_type.value}: {original_input} -> {warnings}")
        
        return ValidationResult(is_valid, sanitized_input, errors, warnings, search_type)
    
    def _sanitize_input(self, input_str: str) -> str:
        """Basic input sanitization"""
        if not input_str:
            return ""
        
        # Remove leading/trailing whitespace
        sanitized = input_str.strip()
        
        # Replace multiple whitespace with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Remove null bytes and control characters except newlines/tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:500]
        
        return sanitized
    
    def _check_security_threats(self, input_str: str) -> List[str]:
        """Check for SQL injection and XSS attempts"""
        errors = []
        input_lower = input_str.lower()
        
        # Check SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                errors.append("Invalid characters detected in search term")
                logger.warning(f"Potential SQL injection attempt: {input_str}")
                break
        
        # Check XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                errors.append("Invalid HTML content detected")
                logger.warning(f"Potential XSS attempt: {input_str}")
                break
        
        return errors
    
    def _validate_apn(self, apn: str) -> Tuple[bool, List[str], List[str]]:
        """Validate APN format"""
        errors = []
        warnings = []
        
        # Remove common separators for validation
        cleaned_apn = re.sub(r'[-\s]', '', apn)
        
        # Check if it matches any APN pattern
        apn_valid = False
        for pattern in self.apn_patterns:
            if re.match(pattern, apn, re.IGNORECASE):
                apn_valid = True
                break
            # Also check cleaned version
            if re.match(pattern, cleaned_apn, re.IGNORECASE):
                apn_valid = True
                warnings.append("APN format cleaned for search")
                break
        
        if not apn_valid:
            # Check if it's potentially an APN but malformed
            if re.match(r'^\d{6,15}[A-Z]?$', cleaned_apn):
                warnings.append("APN format may be non-standard but will be attempted")
                apn_valid = True
            else:
                errors.append("Invalid APN format. Expected format: XXX-XX-XXXX or similar")
        
        # Length check
        if len(cleaned_apn) < 6:
            errors.append("APN too short")
        elif len(cleaned_apn) > 15:
            errors.append("APN too long")
        
        return apn_valid and not errors, errors, warnings
    
    def _validate_owner_name(self, name: str) -> Tuple[bool, List[str], List[str]]:
        """Validate owner name format"""
        errors = []
        warnings = []
        
        # Length check
        if len(name) < 2:
            errors.append("Owner name too short (minimum 2 characters)")
        elif len(name) > 100:
            errors.append("Owner name too long (maximum 100 characters)")
        
        # Character validation
        valid_name = False
        for pattern in self.name_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                valid_name = True
                break
        
        if not valid_name:
            # Check if it contains valid characters but unusual pattern
            if re.match(r"^[A-Za-z0-9\s\.\-',&]+$", name):
                warnings.append("Name contains unusual characters but will be searched")
                valid_name = True
            else:
                errors.append("Name contains invalid characters")
        
        # Check for business indicators
        business_indicators = ['LLC', 'INC', 'CORP', 'LTD', 'COMPANY', 'CO', 'TRUST']
        if any(indicator in name.upper() for indicator in business_indicators):
            warnings.append("Business entity detected - searching as owner name")
        
        return valid_name and not errors, errors, warnings
    
    def _validate_address(self, address: str) -> Tuple[bool, List[str], List[str]]:
        """Validate address format"""
        errors = []
        warnings = []
        
        # Length check
        if len(address) < 5:
            errors.append("Address too short (minimum 5 characters)")
        elif len(address) > 200:
            errors.append("Address too long (maximum 200 characters)")
        
        # Basic address pattern validation
        valid_address = False
        for pattern in self.address_patterns:
            if re.match(pattern, address, re.IGNORECASE):
                valid_address = True
                break
        
        if not valid_address:
            # Flexible validation - if it contains numbers and letters, allow it
            if re.search(r'\d', address) and re.search(r'[A-Za-z]', address):
                warnings.append("Address format is non-standard but will be searched")
                valid_address = True
            else:
                errors.append("Address must contain both numbers and letters")
        
        # Check for common address components
        has_number = bool(re.search(r'^\d+', address.strip()))
        if not has_number:
            warnings.append("Address may be missing house number")
        
        return valid_address and not errors, errors, warnings
    
    def _advanced_sanitization(self, input_str: str, search_type: SearchType) -> str:
        """Advanced sanitization based on search type"""
        sanitized = input_str
        
        if search_type == SearchType.APN:
            # Standardize APN format
            sanitized = re.sub(r'[^\d\-A-Z]', '', sanitized.upper())
            
        elif search_type == SearchType.OWNER:
            # Normalize name format
            sanitized = ' '.join(word.capitalize() for word in sanitized.split())
            
        elif search_type == SearchType.ADDRESS:
            # Normalize address format
            sanitized = ' '.join(word.upper() if word.upper() in 
                               ['ST', 'STREET', 'AVE', 'AVENUE', 'RD', 'ROAD', 'BLVD', 'BOULEVARD', 
                                'DR', 'DRIVE', 'LN', 'LANE', 'CT', 'COURT', 'PL', 'PLACE', 'WAY', 'CIR', 'CIRCLE']
                               else word.title() for word in sanitized.split())
        
        return sanitized
    
    def auto_detect_search_type(self, input_str: str) -> Optional[SearchType]:
        """Auto-detect search type based on input pattern"""
        sanitized = self._sanitize_input(input_str)
        
        # Check APN patterns first (most specific)
        for pattern in self.apn_patterns:
            if re.match(pattern, sanitized, re.IGNORECASE):
                return SearchType.APN
            # Also check without separators
            cleaned = re.sub(r'[-\s]', '', sanitized)
            if re.match(pattern, cleaned, re.IGNORECASE):
                return SearchType.APN
        
        # Check if it looks like an address (has numbers and street indicators)
        if re.search(r'^\d+\s', sanitized) and re.search(r'\b(ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|DR|LN|CT|PL|WAY|CIR)\b', sanitized, re.IGNORECASE):
            return SearchType.ADDRESS
        
        # Check if it looks like a name (letters, spaces, common name chars)
        if re.match(r'^[A-Za-z\s\.\-\'&,]+$', sanitized) and len(sanitized.split()) >= 1:
            return SearchType.OWNER
        
        # If it contains numbers but no street indicators, might be APN
        if re.match(r'^\d{6,}[A-Z]?$', re.sub(r'[-\s]', '', sanitized)):
            return SearchType.APN
        
        return None

    def get_search_suggestions(self, partial_input: str) -> Dict[str, List[str]]:
        """Get search format suggestions based on partial input"""
        suggestions = {
            'apn': [],
            'owner': [], 
            'address': []
        }
        
        if not partial_input or len(partial_input) < 2:
            return {
                'apn': ['123-45-678A', '1234567890', '123-45-6789'],
                'owner': ['Smith John', 'Johnson Mary', 'Brown Family Trust'],
                'address': ['123 Main Street', '456 Oak Avenue', '789 Pine Road']
            }
        
        # APN suggestions
        if re.match(r'^\d', partial_input):
            if '-' in partial_input:
                suggestions['apn'].append(f"{partial_input}...")
            else:
                if len(partial_input) >= 3:
                    suggestions['apn'].append(f"{partial_input[:3]}-{partial_input[3:]}")
        
        # Name suggestions  
        if re.match(r'^[A-Za-z]', partial_input):
            suggestions['owner'].append(f"{partial_input.title()}...")
        
        # Address suggestions
        if re.match(r'^\d', partial_input):
            suggestions['address'].append(f"{partial_input} Main Street")
            suggestions['address'].append(f"{partial_input} Oak Avenue")
        
        return suggestions