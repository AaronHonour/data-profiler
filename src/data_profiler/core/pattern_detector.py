"""Enhanced pattern detection for PII and sensitive data."""

import re
from typing import Dict, List

import pandas as pd


class PatternDetector:
    """Advanced pattern detection for various data formats and PII."""

    # Credit card patterns (Luhn algorithm validation)
    CREDIT_CARD_PATTERNS = {
        "visa": re.compile(r"^4[0-9]{12}(?:[0-9]{3})?$"),
        "mastercard": re.compile(r"^5[1-5][0-9]{14}$"),
        "amex": re.compile(r"^3[47][0-9]{13}$"),
        "discover": re.compile(r"^6(?:011|5[0-9]{2})[0-9]{12}$"),
    }

    # Social Security Number (US)
    SSN_PATTERN = re.compile(r"^(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}$")
    SSN_PATTERN_NO_DASH = re.compile(r"^(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}$")

    # Enhanced patterns
    PATTERNS = {
        # Contact information
        "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "phone_us": re.compile(r"^(\+1[-\s]?)?(\(?\d{3}\)?[-\s]?)?\d{3}[-\s]?\d{4}$"),
        "phone_intl": re.compile(r"^\+[1-9]\d{1,14}$"),
        # Network
        "ipv4": re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"),
        "ipv6": re.compile(r"^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4})$"),
        "mac_address": re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"),
        # Identifiers
        "uuid": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE),
        "md5": re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE),
        "sha1": re.compile(r"^[a-f0-9]{40}$", re.IGNORECASE),
        "sha256": re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE),
        # Web
        "url": re.compile(r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?$"),
        "domain": re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"),
        # Financial
        "iban": re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$"),
        "swift_bic": re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"),
        # Postal codes
        "zip_us": re.compile(r"^\d{5}(-\d{4})?$"),
        "postal_uk": re.compile(r"^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$", re.IGNORECASE),
        # Other
        "hex_color": re.compile(r"^#?([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$"),
        "semver": re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"),
    }

    @staticmethod
    def validate_luhn(number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.

        Args:
            number: Credit card number string

        Returns:
            True if valid, False otherwise
        """
        try:
            digits = [int(d) for d in number if d.isdigit()]
            checksum = 0
            is_second = False

            for i in range(len(digits) - 1, -1, -1):
                d = digits[i]

                if is_second:
                    d = d * 2
                    if d > 9:
                        d = d - 9

                checksum += d
                is_second = not is_second

            return checksum % 10 == 0
        except Exception:
            return False

    @classmethod
    def detect_credit_cards(cls, series: pd.Series, sample_size: int = 1000) -> Dict[str, int]:
        """
        Detect credit card numbers in a series.

        Args:
            series: Pandas series with potential credit card numbers
            sample_size: Number of values to sample

        Returns:
            Dictionary with counts by card type
        """
        results = {}
        sample = series.dropna().astype(str).sample(n=min(sample_size, len(series)), random_state=42)

        for card_type, pattern in cls.CREDIT_CARD_PATTERNS.items():
            matches = sample.str.replace(r"[- ]", "", regex=True).str.match(pattern)
            valid_count = 0

            for idx in sample[matches].index:
                number = str(sample[idx]).replace("-", "").replace(" ", "")
                if cls.validate_luhn(number):
                    valid_count += 1

            if valid_count > 0:
                # Extrapolate to full dataset
                estimated = int((valid_count / len(sample)) * len(series))
                results[card_type] = estimated

        return results

    @classmethod
    def detect_ssn(cls, series: pd.Series, sample_size: int = 1000) -> int:
        """
        Detect Social Security Numbers.

        Args:
            series: Pandas series with potential SSNs
            sample_size: Number of values to sample

        Returns:
            Estimated count of SSNs
        """
        sample = series.dropna().astype(str).sample(n=min(sample_size, len(series)), random_state=42)

        # Try both formats
        matches_dash = sample.str.match(cls.SSN_PATTERN)
        matches_no_dash = sample.str.match(cls.SSN_PATTERN_NO_DASH)

        match_count = int((matches_dash | matches_no_dash).sum())

        if match_count > 0:
            return int((match_count / len(sample)) * len(series))

        return 0

    @classmethod
    def detect_all_patterns(cls, series: pd.Series, sample_size: int = 1000) -> Dict[str, int]:
        """
        Detect all patterns in a series.

        Args:
            series: Pandas series to analyze
            sample_size: Number of values to sample

        Returns:
            Dictionary with pattern counts
        """
        results = {}
        sample = series.dropna().astype(str).sample(n=min(sample_size, len(series)), random_state=42)

        # Standard patterns
        for pattern_name, pattern_regex in cls.PATTERNS.items():
            matches = sample.str.match(pattern_regex, na=False)
            match_count = int(matches.sum())

            if match_count > 0:
                estimated = int((match_count / len(sample)) * len(series))
                results[pattern_name] = estimated

        # Credit cards (with Luhn validation)
        credit_cards = cls.detect_credit_cards(series, sample_size)
        if credit_cards:
            results["credit_cards"] = credit_cards

        # SSN
        ssn_count = cls.detect_ssn(series, sample_size)
        if ssn_count > 0:
            results["ssn"] = ssn_count

        return results

    @staticmethod
    def detect_pii_risk(patterns: Dict[str, int]) -> str:
        """
        Assess PII risk level based on detected patterns.

        Args:
            patterns: Dictionary of detected patterns

        Returns:
            Risk level: "high", "medium", "low", or "none"
        """
        high_risk_patterns = {"ssn", "credit_cards"}
        medium_risk_patterns = {"email", "phone_us", "phone_intl"}

        if any(p in patterns for p in high_risk_patterns):
            return "high"
        elif any(p in patterns for p in medium_risk_patterns):
            return "medium"
        elif len(patterns) > 0:
            return "low"
        else:
            return "none"
