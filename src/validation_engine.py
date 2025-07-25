"""
Main validation engine for the String Validation Tool.

This module contains the core validation logic that orchestrates OCR processing,
string matching, and result reporting using dependency injection and observer patterns.
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

from .interfaces import OCREngine, StringMatcher, DataLoader, ValidationObserver
from .models import (
    ValidationConfig, ValidationResult, TestStep, Coordinate, 
    MatchResult, OCRConfig
)
from .exceptions import ValidationError, OCRError, ImageProcessingError
from .data_loaders import DataLoaderFactory
from .ocr_engines import OCREngineFactory
from .matchers import StringMatcherFactory

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Main validation engine that orchestrates the validation process.
    
    This class uses dependency injection to allow flexible configuration
    of OCR engines, string matchers, and data loaders.
    """
    
    def __init__(
        self,
        config: ValidationConfig,
        ocr_engine: Optional[OCREngine] = None,
        string_matcher: Optional[StringMatcher] = None,
        data_loader: Optional[DataLoader] = None
    ):
        """
        Initialize the validation engine.
        
        Args:
            config: Validation configuration
            ocr_engine: OCR engine instance (uses default if None)
            string_matcher: String matcher instance (uses default if None)
            data_loader: Data loader instance (uses default if None)
        """
        self.config = config
        self.ocr_engine = ocr_engine or OCREngineFactory.create_engine()
        self.string_matcher = string_matcher or StringMatcherFactory.create_default_matcher(
            fuzzy_threshold=config.fuzzy_matching_threshold
        )
        self.data_loader = data_loader or DataLoaderFactory.create_loader()
        
        # Observer pattern for progress tracking
        self._observers: List[ValidationObserver] = []
        
        # Cached data
        self._test_steps: Optional[List[TestStep]] = None
        self._expected_strings: Optional[Dict[str, str]] = None
        self._coordinates: Optional[Dict[Tuple[str, str, str], Coordinate]] = None
        
        # Setup logging
        self._setup_logging()
    
    def add_observer(self, observer: ValidationObserver) -> None:
        """Add a validation observer."""
        self._observers.append(observer)
    
    def remove_observer(self, observer: ValidationObserver) -> None:
        """Remove a validation observer."""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify_validation_start(self, total_steps: int) -> None:
        """Notify observers that validation has started."""
        for observer in self._observers:
            try:
                observer.on_validation_start(total_steps)
            except Exception as e:
                logger.error(f"Error in observer notification: {str(e)}")
    
    def _notify_step_complete(self, result: ValidationResult) -> None:
        """Notify observers that a validation step has completed."""
        for observer in self._observers:
            try:
                observer.on_step_complete(result)
            except Exception as e:
                logger.error(f"Error in observer notification: {str(e)}")
    
    def _notify_validation_complete(self, results: List[ValidationResult]) -> None:
        """Notify observers that validation has completed."""
        for observer in self._observers:
            try:
                observer.on_validation_complete(results)
            except Exception as e:
                logger.error(f"Error in observer notification: {str(e)}")
    
    def _notify_error(self, error: Exception, step: Optional[TestStep] = None) -> None:
        """Notify observers of an error."""
        for observer in self._observers:
            try:
                observer.on_error(error, step)
            except Exception as e:
                logger.error(f"Error in observer notification: {str(e)}")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    @contextmanager
    def _load_data(self):
        """Context manager for loading and caching validation data."""
        try:
            logger.info("Loading validation data...")
            
            # Load test protocol
            self._test_steps = self.data_loader.load_test_protocol(
                str(self.config.protocol_file)
            )
            
            # Load expected strings
            self._expected_strings = self.data_loader.load_expected_strings(
                str(self.config.string_map_file)
            )
            
            # Load coordinates
            self._coordinates = self.data_loader.load_coordinates(
                str(self.config.coordinate_file)
            )
            
            logger.info("Data loading completed successfully")
            yield
            
        except Exception as e:
            logger.error(f"Failed to load validation data: {str(e)}")
            raise ValidationError(f"Data loading failed: {str(e)}")
        finally:
            # Clear cached data
            self._test_steps = None
            self._expected_strings = None
            self._coordinates = None
    
    def validate_all(self) -> List[ValidationResult]:
        """
        Run validation for all test steps.
        
        Returns:
            List of validation results
            
        Raises:
            ValidationError: If validation fails
        """
        with self._load_data():
            if not self._test_steps:
                raise ValidationError("No test steps loaded")
            
            results = []
            self._notify_validation_start(len(self._test_steps))
            
            try:
                for step in self._test_steps:
                    try:
                        result = self._validate_step(step)
                        results.append(result)
                        self._notify_step_complete(result)
                        
                    except Exception as e:
                        logger.error(f"Error validating step {step.step_id}: {str(e)}")
                        self._notify_error(e, step)
                        
                        # Create error result
                        error_result = ValidationResult(
                            step=step,
                            expected_text="",
                            ocr_output="",
                            match_result=MatchResult.ERROR,
                            error_message=str(e)
                        )
                        results.append(error_result)
                        self._notify_step_complete(error_result)
                
                self._notify_validation_complete(results)
                return results
                
            except Exception as e:
                logger.error(f"Validation process failed: {str(e)}")
                self._notify_error(e)
                raise ValidationError(f"Validation process failed: {str(e)}")
    
    def validate_step(self, step: TestStep) -> ValidationResult:
        """
        Validate a single test step.
        
        Args:
            step: Test step to validate
            
        Returns:
            Validation result
            
        Raises:
            ValidationError: If validation fails
        """
        with self._load_data():
            return self._validate_step(step)
    
    def _validate_step(self, step: TestStep) -> ValidationResult:
        """
        Internal method to validate a single step.
        
        Args:
            step: Test step to validate
            
        Returns:
            Validation result
        """
        start_time = time.time()
        
        try:
            # Get expected text
            expected_text = self._expected_strings.get(step.expected_string_id, "")
            if not expected_text:
                return ValidationResult(
                    step=step,
                    expected_text="",
                    ocr_output="",
                    match_result=MatchResult.ERROR,
                    error_message=f"Expected string not found: {step.expected_string_id}"
                )
            
            # Get image path
            image_path = self.config.screenshot_dir / f"{step.screen_id}.png"
            if not image_path.exists():
                return ValidationResult(
                    step=step,
                    expected_text=expected_text,
                    ocr_output="",
                    match_result=MatchResult.MISSING_IMAGE,
                    error_message=f"Image not found: {image_path}"
                )
            
            # Get coordinates
            coordinate = self._coordinates.get(step.coordinate_key)
            if not coordinate:
                return ValidationResult(
                    step=step,
                    expected_text=expected_text,
                    ocr_output="",
                    match_result=MatchResult.MISSING_COORDINATES,
                    error_message=f"Coordinates not found for: {step.coordinate_key}"
                )
            
            # Perform OCR
            ocr_output, ocr_confidence = self._extract_text_from_region(
                image_path, coordinate
            )
            
            # Perform string matching
            is_match, match_confidence = self.string_matcher.match(expected_text, ocr_output)
            
            # Determine result
            match_result = MatchResult.PASS if is_match else MatchResult.FAIL
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return ValidationResult(
                step=step,
                expected_text=expected_text,
                ocr_output=ocr_output,
                match_result=match_result,
                confidence_score=min(ocr_confidence, match_confidence),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Error validating step {step.step_id}: {str(e)}")
            
            return ValidationResult(
                step=step,
                expected_text=expected_text if 'expected_text' in locals() else "",
                ocr_output="",
                match_result=MatchResult.ERROR,
                processing_time_ms=processing_time,
                error_message=str(e)
            )
    
    def _extract_text_from_region(self, image_path: Path, coordinate: Coordinate) -> Tuple[str, float]:
        """
        Extract text from a specific region of an image.
        
        Args:
            image_path: Path to the image file
            coordinate: Bounding box coordinate
            
        Returns:
            Tuple of (extracted_text, confidence_score)
            
        Raises:
            OCRError: If OCR extraction fails
            ImageProcessingError: If image processing fails
        """
        try:
            # Load and crop image
            with Image.open(image_path) as img:
                cropped_img = img.crop(coordinate.to_tuple())
                
                # Create OCR config
                ocr_config = OCRConfig(
                    language=self.config.language.split('-')[0] if '-' in self.config.language else 'eng',
                    config=self.config.tesseract_config or "--psm 8",
                    preprocessing_enabled=self.config.enable_preprocessing
                )
                
                # Extract text with confidence
                return self.ocr_engine.extract_text_with_confidence(cropped_img, ocr_config)
                
        except FileNotFoundError:
            raise ImageProcessingError(f"Image file not found: {image_path}")
        except Exception as e:
            raise OCRError(f"Failed to extract text from region: {str(e)}", str(image_path))
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict:
        """
        Generate a summary of validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Dictionary containing summary statistics
        """
        if not results:
            return {
                'total_steps': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'missing_images': 0,
                'missing_coordinates': 0,
                'pass_rate': 0.0,
                'average_confidence': 0.0,
                'average_processing_time_ms': 0.0
            }
        
        # Count results by type
        passed = sum(1 for r in results if r.match_result == MatchResult.PASS)
        failed = sum(1 for r in results if r.match_result == MatchResult.FAIL)
        errors = sum(1 for r in results if r.match_result == MatchResult.ERROR)
        missing_images = sum(1 for r in results if r.match_result == MatchResult.MISSING_IMAGE)
        missing_coordinates = sum(1 for r in results if r.match_result == MatchResult.MISSING_COORDINATES)
        
        # Calculate averages
        valid_results = [r for r in results if r.confidence_score is not None]
        avg_confidence = (
            sum(r.confidence_score for r in valid_results) / len(valid_results)
            if valid_results else 0.0
        )
        
        timed_results = [r for r in results if r.processing_time_ms is not None]
        avg_processing_time = (
            sum(r.processing_time_ms for r in timed_results) / len(timed_results)
            if timed_results else 0.0
        )
        
        return {
            'total_steps': len(results),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'missing_images': missing_images,
            'missing_coordinates': missing_coordinates,
            'pass_rate': passed / len(results) * 100.0,
            'average_confidence': avg_confidence,
            'average_processing_time_ms': avg_processing_time
        }