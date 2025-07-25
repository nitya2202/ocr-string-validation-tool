"""
String matching implementations for the String Validation Tool.

This module provides various string matching strategies with different
levels of tolerance and normalization.
"""

import re
import logging
from typing import Tuple
from difflib import SequenceMatcher

from .interfaces import StringMatcher
from .exceptions import MatchingError

logger = logging.getLogger(__name__)


class ExactMatcher(StringMatcher):
    """Exact string matching with case sensitivity options."""
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize exact matcher.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Perform exact string matching.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            expected_clean = expected.strip()
            actual_clean = actual.strip()
            
            if not self.case_sensitive:
                expected_clean = expected_clean.lower()
                actual_clean = actual_clean.lower()
            
            is_match = expected_clean == actual_clean
            confidence = 1.0 if is_match else 0.0
            
            return is_match, confidence
            
        except Exception as e:
            raise MatchingError(f"Exact matching failed: {str(e)}", expected, actual)


class FuzzyMatcher(StringMatcher):
    """Fuzzy string matching using sequence similarity."""
    
    def __init__(self, threshold: float = 0.8, case_sensitive: bool = False):
        """
        Initialize fuzzy matcher.
        
        Args:
            threshold: Minimum similarity threshold (0.0 to 1.0)
            case_sensitive: Whether to perform case-sensitive matching
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.threshold = threshold
        self.case_sensitive = case_sensitive
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Perform fuzzy string matching using sequence similarity.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            expected_clean = expected.strip()
            actual_clean = actual.strip()
            
            if not self.case_sensitive:
                expected_clean = expected_clean.lower()
                actual_clean = actual_clean.lower()
            
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, expected_clean, actual_clean).ratio()
            is_match = similarity >= self.threshold
            
            return is_match, similarity
            
        except Exception as e:
            raise MatchingError(f"Fuzzy matching failed: {str(e)}", expected, actual)


class NormalizedMatcher(StringMatcher):
    """String matching with text normalization."""
    
    def __init__(self, threshold: float = 0.9, normalize_whitespace: bool = True,
                 normalize_punctuation: bool = True, case_sensitive: bool = False):
        """
        Initialize normalized matcher.
        
        Args:
            threshold: Minimum similarity threshold (0.0 to 1.0)
            normalize_whitespace: Whether to normalize whitespace
            normalize_punctuation: Whether to remove punctuation
            case_sensitive: Whether to perform case-sensitive matching
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        
        self.threshold = threshold
        self.normalize_whitespace = normalize_whitespace
        self.normalize_punctuation = normalize_punctuation
        self.case_sensitive = case_sensitive
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Perform normalized string matching.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            expected_normalized = self._normalize_text(expected)
            actual_normalized = self._normalize_text(actual)
            
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, expected_normalized, actual_normalized).ratio()
            is_match = similarity >= self.threshold
            
            return is_match, similarity
            
        except Exception as e:
            raise MatchingError(f"Normalized matching failed: {str(e)}", expected, actual)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text according to configuration.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text
        """
        normalized = text.strip()
        
        if not self.case_sensitive:
            normalized = normalized.lower()
        
        if self.normalize_whitespace:
            # Replace multiple whitespace with single space
            normalized = re.sub(r'\s+', ' ', normalized)
        
        if self.normalize_punctuation:
            # Remove punctuation except spaces
            normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized.strip()


class ContainsMatcher(StringMatcher):
    """String matching that checks if expected text is contained in actual text."""
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize contains matcher.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Check if expected string is contained in actual string.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            expected_clean = expected.strip()
            actual_clean = actual.strip()
            
            if not self.case_sensitive:
                expected_clean = expected_clean.lower()
                actual_clean = actual_clean.lower()
            
            is_match = expected_clean in actual_clean
            
            # Calculate confidence based on length ratio
            if is_match and expected_clean:
                confidence = len(expected_clean) / len(actual_clean) if actual_clean else 0.0
                confidence = min(confidence, 1.0)  # Cap at 1.0
            else:
                confidence = 0.0
            
            return is_match, confidence
            
        except Exception as e:
            raise MatchingError(f"Contains matching failed: {str(e)}", expected, actual)


class RegexMatcher(StringMatcher):
    """String matching using regular expressions."""
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize regex matcher.
        
        Args:
            case_sensitive: Whether to perform case-sensitive matching
        """
        self.case_sensitive = case_sensitive
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Match using expected string as regex pattern.
        
        Args:
            expected: The expected string (treated as regex pattern)
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            flags = 0 if self.case_sensitive else re.IGNORECASE
            
            pattern = re.compile(expected.strip(), flags)
            match = pattern.search(actual.strip())
            
            is_match = match is not None
            
            # Calculate confidence based on match length vs total length
            if is_match and match:
                confidence = len(match.group(0)) / len(actual.strip()) if actual.strip() else 0.0
                confidence = min(confidence, 1.0)  # Cap at 1.0
            else:
                confidence = 0.0
            
            return is_match, confidence
            
        except re.error as e:
            logger.warning(f"Invalid regex pattern '{expected}': {str(e)}")
            # Fallback to exact matching
            exact_matcher = ExactMatcher(self.case_sensitive)
            return exact_matcher.match(expected, actual)
        except Exception as e:
            raise MatchingError(f"Regex matching failed: {str(e)}", expected, actual)


class CompositeMatcher(StringMatcher):
    """Composite matcher that tries multiple matching strategies."""
    
    def __init__(self, matchers: list[StringMatcher], require_all: bool = False):
        """
        Initialize composite matcher.
        
        Args:
            matchers: List of string matchers to use
            require_all: If True, all matchers must pass; if False, any matcher can pass
        """
        if not matchers:
            raise ValueError("At least one matcher must be provided")
        
        self.matchers = matchers
        self.require_all = require_all
    
    def match(self, expected: str, actual: str) -> Tuple[bool, float]:
        """
        Apply multiple matching strategies.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            results = []
            
            for matcher in self.matchers:
                is_match, confidence = matcher.match(expected, actual)
                results.append((is_match, confidence))
            
            if self.require_all:
                # All matchers must pass
                overall_match = all(result[0] for result in results)
                # Use minimum confidence if all pass, 0.0 otherwise
                overall_confidence = min(result[1] for result in results) if overall_match else 0.0
            else:
                # Any matcher can pass
                overall_match = any(result[0] for result in results)
                # Use maximum confidence from passing matchers
                passing_confidences = [result[1] for result in results if result[0]]
                overall_confidence = max(passing_confidences) if passing_confidences else 0.0
            
            return overall_match, overall_confidence
            
        except Exception as e:
            raise MatchingError(f"Composite matching failed: {str(e)}", expected, actual)


class StringMatcherFactory:
    """Factory for creating string matchers."""
    
    _matchers = {
        'exact': ExactMatcher,
        'fuzzy': FuzzyMatcher,
        'normalized': NormalizedMatcher,
        'contains': ContainsMatcher,
        'regex': RegexMatcher,
    }
    
    @classmethod
    def create_matcher(cls, matcher_type: str, **kwargs) -> StringMatcher:
        """
        Create a string matcher instance.
        
        Args:
            matcher_type: Type of matcher ('exact', 'fuzzy', 'normalized', 'contains', 'regex')
            **kwargs: Additional arguments for the matcher
            
        Returns:
            String matcher instance
            
        Raises:
            ValueError: If matcher type is not supported
        """
        if matcher_type not in cls._matchers:
            raise ValueError(f"Unsupported matcher type: {matcher_type}. "
                           f"Available matchers: {list(cls._matchers.keys())}")
        
        return cls._matchers[matcher_type](**kwargs)
    
    @classmethod
    def create_default_matcher(cls, fuzzy_threshold: float = 0.8) -> StringMatcher:
        """
        Create a default composite matcher with common strategies.
        
        Args:
            fuzzy_threshold: Threshold for fuzzy matching
            
        Returns:
            Composite string matcher
        """
        matchers = [
            ExactMatcher(case_sensitive=False),
            NormalizedMatcher(threshold=0.9, case_sensitive=False),
            FuzzyMatcher(threshold=fuzzy_threshold, case_sensitive=False),
        ]
        
        return CompositeMatcher(matchers, require_all=False)
    
    @classmethod
    def get_available_matchers(cls) -> list[str]:
        """Get list of available matcher types."""
        return list(cls._matchers.keys())