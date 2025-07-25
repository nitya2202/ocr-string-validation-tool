"""
Abstract interfaces for the OCR String Validation Tool.

This module defines abstract base classes that establish contracts
for different components, enabling the use of strategy pattern and
dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from PIL import Image

from .models import Coordinate, ValidationResult, TestStep, OCRConfig


class OCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    @abstractmethod
    def extract_text(self, image: Image.Image, config: Optional[OCRConfig] = None) -> str:
        """
        Extract text from an image.
        
        Args:
            image: PIL Image object
            config: OCR configuration options
            
        Returns:
            Extracted text as string
        """
        pass
    
    @abstractmethod
    def extract_text_with_confidence(self, image: Image.Image, 
                                   config: Optional[OCRConfig] = None) -> tuple[str, float]:
        """
        Extract text from an image with confidence score.
        
        Args:
            image: PIL Image object
            config: OCR configuration options
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        pass


class StringMatcher(ABC):
    """Abstract base class for string matching strategies."""
    
    @abstractmethod
    def match(self, expected: str, actual: str) -> tuple[bool, float]:
        """
        Compare two strings and return match result with confidence.
        
        Args:
            expected: The expected string
            actual: The actual string from OCR
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        pass


class ImagePreprocessor(ABC):
    """Abstract base class for image preprocessing strategies."""
    
    @abstractmethod
    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Preprocess an image to improve OCR accuracy.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        pass


class ValidationObserver(Protocol):
    """Protocol for validation progress observers."""
    
    def on_validation_start(self, total_steps: int) -> None:
        """Called when validation starts."""
        ...
    
    def on_step_complete(self, result: ValidationResult) -> None:
        """Called when a validation step completes."""
        ...
    
    def on_validation_complete(self, results: List[ValidationResult]) -> None:
        """Called when validation completes."""
        ...
    
    def on_error(self, error: Exception, step: Optional[TestStep] = None) -> None:
        """Called when an error occurs."""
        ...


class DataLoader(ABC):
    """Abstract base class for data loading strategies."""
    
    @abstractmethod
    def load_test_protocol(self, file_path: str) -> List[TestStep]:
        """Load test protocol from file."""
        pass
    
    @abstractmethod
    def load_expected_strings(self, file_path: str) -> dict[str, str]:
        """Load expected strings mapping from file."""
        pass
    
    @abstractmethod
    def load_coordinates(self, file_path: str) -> dict[tuple[str, str, str], Coordinate]:
        """Load coordinate mappings from file."""
        pass


class ReportGenerator(ABC):
    """Abstract base class for report generation strategies."""
    
    @abstractmethod
    def generate_report(self, results: List[ValidationResult], output_path: str) -> None:
        """Generate validation report."""
        pass
    
    @abstractmethod
    def get_summary_stats(self, results: List[ValidationResult]) -> dict:
        """Get summary statistics from results."""
        pass