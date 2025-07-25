"""
OCR String Validation Tool - Refactored Architecture

A modular, production-ready framework for automated string validation
using OCR technology with configurable matching strategies.
"""

__version__ = "2.0.0"
__author__ = "OCR Validation Team"

# Core exports
from .models import ValidationConfig, ValidationResult, TestStep, Coordinate, MatchResult
from .validation_engine import ValidationEngine
from .annotation_tool import AnnotationTool

# Factory exports
from .ocr_engines import OCREngineFactory
from .matchers import StringMatcherFactory
from .data_loaders import DataLoaderFactory
from .reporters import ReportGeneratorFactory

__all__ = [
    'ValidationConfig',
    'ValidationResult', 
    'TestStep',
    'Coordinate',
    'MatchResult',
    'ValidationEngine',
    'AnnotationTool',
    'OCREngineFactory',
    'StringMatcherFactory',
    'DataLoaderFactory',
    'ReportGeneratorFactory',
]