"""
Custom exceptions for the OCR String Validation Tool.

This module defines domain-specific exceptions that provide better
error handling and debugging capabilities.
"""

from typing import Optional


class ValidationError(Exception):
    """Base exception for validation-related errors."""
    
    def __init__(self, message: str, step_id: Optional[str] = None, 
                 screen_id: Optional[str] = None):
        super().__init__(message)
        self.step_id = step_id
        self.screen_id = screen_id
        self.message = message


class OCRError(ValidationError):
    """Exception raised when OCR processing fails."""
    
    def __init__(self, message: str, image_path: Optional[str] = None,
                 step_id: Optional[str] = None, screen_id: Optional[str] = None):
        super().__init__(message, step_id, screen_id)
        self.image_path = image_path


class ConfigurationError(ValidationError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message)
        self.config_key = config_key


class DataLoadError(ValidationError):
    """Exception raised when data loading fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path


class AnnotationError(ValidationError):
    """Exception raised during annotation operations."""
    
    def __init__(self, message: str, screen_id: Optional[str] = None):
        super().__init__(message, screen_id=screen_id)


class ImageProcessingError(ValidationError):
    """Exception raised during image processing operations."""
    
    def __init__(self, message: str, image_path: Optional[str] = None,
                 coordinate: Optional[str] = None):
        super().__init__(message)
        self.image_path = image_path
        self.coordinate = coordinate


class MatchingError(ValidationError):
    """Exception raised during string matching operations."""
    
    def __init__(self, message: str, expected_text: Optional[str] = None,
                 actual_text: Optional[str] = None):
        super().__init__(message)
        self.expected_text = expected_text
        self.actual_text = actual_text