"""Custom pattern detection with user-defined regex."""

import re
from typing import Dict, List, Optional

import pandas as pd
from pydantic import BaseModel, Field


class CustomPattern(BaseModel):
    """User-defined pattern for detection."""

    name: str = Field(description="Pattern name/identifier")
    regex: str = Field(description="Regular expression pattern")
    description: Optional[str] = Field(None, description="Pattern description")
    category: Optional[str] = Field(None, description="Pattern category (e.g., 'business', 'custom')")
    case_sensitive: bool = Field(True, description="Whether pattern is case-sensitive")
    examples: List[str] = Field(default_factory=list, description="Example values that match")

    def compile(self) -> re.Pattern:
        """Compile the regex pattern."""
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return re.compile(self.regex, flags)


class PatternLibrary(BaseModel):
    """Collection of custom patterns."""

    name: str = Field(description="Library name")
    description: Optional[str] = None
    patterns: List[CustomPattern] = Field(default_factory=list)

    def add_pattern(self, pattern: CustomPattern) -> None:
        """Add a pattern to the library."""
        self.patterns.append(pattern)

    def get_pattern(self, name: str) -> Optional[CustomPattern]:
        """Get a pattern by name."""
        return next((p for p in self.patterns if p.name == name), None)


class CustomPatternDetector:
    """Detect custom user-defined patterns in data."""

    @staticmethod
    def detect_patterns(
        series: pd.Series,
        patterns: List[CustomPattern],
        sample_size: int = 1000,
    ) -> Dict[str, int]:
        """
        Detect custom patterns in a pandas series.

        Args:
            series: Pandas series to analyze
            patterns: List of custom patterns to detect
            sample_size: Number of values to sample

        Returns:
            Dictionary mapping pattern names to estimated counts
        """
        results = {}

        # Drop nulls and convert to string
        clean_data = series.dropna().astype(str)

        if len(clean_data) == 0:
            return results

        # Sample for performance
        sample = clean_data.sample(n=min(sample_size, len(clean_data)), random_state=42)

        for pattern in patterns:
            try:
                # Compile regex
                regex = pattern.compile()

                # Vectorized pattern matching
                matches = sample.str.match(regex, na=False)
                match_count = int(matches.sum())

                if match_count > 0:
                    # Extrapolate to full dataset
                    estimated_count = int((match_count / len(sample)) * len(clean_data))
                    results[pattern.name] = estimated_count

            except Exception as e:
                # Log error but continue with other patterns
                print(f"Error detecting pattern '{pattern.name}': {e}")
                continue

        return results

    @staticmethod
    def validate_pattern(pattern: CustomPattern, test_values: List[str]) -> Dict[str, bool]:
        """
        Validate a pattern against test values.

        Args:
            pattern: Pattern to validate
            test_values: List of test values

        Returns:
            Dictionary mapping test values to match results
        """
        regex = pattern.compile()
        return {value: bool(regex.match(value)) for value in test_values}

    @staticmethod
    def create_business_patterns() -> PatternLibrary:
        """
        Create a library of common business-specific patterns.

        Returns:
            PatternLibrary with business patterns
        """
        library = PatternLibrary(
            name="Business Patterns",
            description="Common business and domain-specific patterns"
        )

        # Order number pattern
        library.add_pattern(CustomPattern(
            name="order_number",
            regex=r"^ORD-\d{6,10}$",
            description="Order number format: ORD-XXXXXX",
            category="business",
            examples=["ORD-123456", "ORD-9876543210"]
        ))

        # Customer ID pattern
        library.add_pattern(CustomPattern(
            name="customer_id",
            regex=r"^CUST-[A-Z0-9]{8}$",
            description="Customer ID format: CUST-XXXXXXXX",
            category="business",
            examples=["CUST-A1B2C3D4", "CUST-12345678"]
        ))

        # Invoice number
        library.add_pattern(CustomPattern(
            name="invoice_number",
            regex=r"^INV-\d{4}-\d{6}$",
            description="Invoice number format: INV-YYYY-XXXXXX",
            category="business",
            examples=["INV-2024-123456", "INV-2023-999999"]
        ))

        # Product SKU
        library.add_pattern(CustomPattern(
            name="product_sku",
            regex=r"^[A-Z]{2,4}-\d{4,8}$",
            description="Product SKU format: XX-XXXX",
            category="business",
            examples=["PROD-12345", "SKU-99887766"]
        ))

        # License plate (US)
        library.add_pattern(CustomPattern(
            name="license_plate_us",
            regex=r"^[A-Z]{2,3}[-\s]?\d{3,4}$",
            description="US license plate format",
            category="automotive",
            case_sensitive=False,
            examples=["ABC-1234", "XY 567"]
        ))

        # VIN (Vehicle Identification Number)
        library.add_pattern(CustomPattern(
            name="vin",
            regex=r"^[A-HJ-NPR-Z0-9]{17}$",
            description="Vehicle Identification Number (17 characters)",
            category="automotive",
            case_sensitive=False,
            examples=["1HGBH41JXMN109186"]
        ))

        # ISBN-10
        library.add_pattern(CustomPattern(
            name="isbn_10",
            regex=r"^(?:\d{9}X|\d{10})$",
            description="ISBN-10 book identifier",
            category="publishing",
            examples=["0123456789", "123456789X"]
        ))

        # ISBN-13
        library.add_pattern(CustomPattern(
            name="isbn_13",
            regex=r"^97[89]\d{10}$",
            description="ISBN-13 book identifier",
            category="publishing",
            examples=["9780123456789"]
        ))

        # Tracking number (FedEx)
        library.add_pattern(CustomPattern(
            name="fedex_tracking",
            regex=r"^\d{12}$|^\d{15}$|^\d{20}$",
            description="FedEx tracking number",
            category="logistics",
            examples=["123456789012", "123456789012345"]
        ))

        # Tracking number (UPS)
        library.add_pattern(CustomPattern(
            name="ups_tracking",
            regex=r"^1Z[A-Z0-9]{16}$",
            description="UPS tracking number",
            category="logistics",
            case_sensitive=False,
            examples=["1Z999AA10123456784"]
        ))

        return library

    @staticmethod
    def create_medical_patterns() -> PatternLibrary:
        """
        Create a library of medical/healthcare patterns.

        Returns:
            PatternLibrary with medical patterns
        """
        library = PatternLibrary(
            name="Medical Patterns",
            description="Healthcare and medical data patterns"
        )

        # NPI (National Provider Identifier)
        library.add_pattern(CustomPattern(
            name="npi",
            regex=r"^\d{10}$",
            description="National Provider Identifier (10 digits)",
            category="medical",
            examples=["1234567890"]
        ))

        # ICD-10 code
        library.add_pattern(CustomPattern(
            name="icd10",
            regex=r"^[A-Z]\d{2}(?:\.[A-Z0-9]{1,4})?$",
            description="ICD-10 diagnosis code",
            category="medical",
            examples=["A01", "Z99.89", "S72.001A"]
        ))

        # Medical Record Number (MRN)
        library.add_pattern(CustomPattern(
            name="mrn",
            regex=r"^MRN-\d{7,10}$",
            description="Medical Record Number",
            category="medical",
            examples=["MRN-1234567", "MRN-9876543210"]
        ))

        # Drug NDC (National Drug Code)
        library.add_pattern(CustomPattern(
            name="ndc",
            regex=r"^\d{4,5}-\d{3,4}-\d{1,2}$",
            description="National Drug Code",
            category="medical",
            examples=["12345-678-90", "1234-5678-1"]
        ))

        return library

    @staticmethod
    def create_financial_patterns() -> PatternLibrary:
        """
        Create a library of financial patterns.

        Returns:
            PatternLibrary with financial patterns
        """
        library = PatternLibrary(
            name="Financial Patterns",
            description="Financial and banking patterns"
        )

        # Account number (generic)
        library.add_pattern(CustomPattern(
            name="account_number",
            regex=r"^ACC-\d{8,12}$",
            description="Generic account number",
            category="financial",
            examples=["ACC-12345678", "ACC-123456789012"]
        ))

        # Routing number (US)
        library.add_pattern(CustomPattern(
            name="routing_number",
            regex=r"^\d{9}$",
            description="US bank routing number (9 digits)",
            category="financial",
            examples=["123456789"]
        ))

        # CUSIP
        library.add_pattern(CustomPattern(
            name="cusip",
            regex=r"^[A-Z0-9]{9}$",
            description="CUSIP security identifier",
            category="financial",
            examples=["037833100"]
        ))

        # Transaction ID
        library.add_pattern(CustomPattern(
            name="transaction_id",
            regex=r"^TXN-[A-Z0-9]{16}$",
            description="Transaction identifier",
            category="financial",
            examples=["TXN-A1B2C3D4E5F6G7H8"]
        ))

        return library
