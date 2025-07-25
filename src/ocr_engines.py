"""
OCR engine implementations for the String Validation Tool.

This module provides concrete implementations of OCR engines using
different libraries and strategies.
"""

import logging
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import cv2

from .interfaces import OCREngine, ImagePreprocessor
from .models import OCRConfig
from .exceptions import OCRError, ImageProcessingError

logger = logging.getLogger(__name__)


class BasicImagePreprocessor(ImagePreprocessor):
    """Basic image preprocessing for better OCR accuracy."""
    
    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Apply basic preprocessing: grayscale, contrast enhancement, and noise reduction.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Resize if image is too small (OCR works better on larger images)
            width, height = image.size
            if width < 100 or height < 30:
                scale_factor = max(100 / width, 30 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to preprocess image: {str(e)}")


class AdvancedImagePreprocessor(ImagePreprocessor):
    """Advanced image preprocessing using OpenCV."""
    
    def preprocess(self, image: Image.Image) -> Image.Image:
        """
        Apply advanced preprocessing using OpenCV operations.
        
        Args:
            image: Input PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL
            return Image.fromarray(cleaned)
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to preprocess image with OpenCV: {str(e)}")


class TesseractOCREngine(OCREngine):
    """OCR engine using Tesseract."""
    
    def __init__(self, preprocessor: Optional[ImagePreprocessor] = None):
        """
        Initialize Tesseract OCR engine.
        
        Args:
            preprocessor: Optional image preprocessor
        """
        self.preprocessor = preprocessor or BasicImagePreprocessor()
        
        # Verify Tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise OCRError(f"Tesseract not found or not properly configured: {str(e)}")
    
    def extract_text(self, image: Image.Image, config: Optional[OCRConfig] = None) -> str:
        """
        Extract text from image using Tesseract.
        
        Args:
            image: PIL Image object
            config: OCR configuration options
            
        Returns:
            Extracted text as string
        """
        try:
            # Apply preprocessing
            processed_image = self.preprocessor.preprocess(image)
            
            # Prepare Tesseract config
            tesseract_config = self._build_tesseract_config(config)
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                lang=config.language if config else 'eng',
                config=tesseract_config
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise OCRError(f"Failed to extract text: {str(e)}")
    
    def extract_text_with_confidence(self, image: Image.Image, 
                                   config: Optional[OCRConfig] = None) -> Tuple[str, float]:
        """
        Extract text with confidence score using Tesseract.
        
        Args:
            image: PIL Image object
            config: OCR configuration options
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Apply preprocessing
            processed_image = self.preprocessor.preprocess(image)
            
            # Prepare Tesseract config
            tesseract_config = self._build_tesseract_config(config)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                processed_image,
                lang=config.language if config else 'eng',
                config=tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate average confidence
            words = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Filter out low-confidence detections
                    word = data['text'][i].strip()
                    if word:
                        words.append(word)
                        confidences.append(int(conf))
            
            text = ' '.join(words)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return text, avg_confidence / 100.0  # Convert to 0-1 scale
            
        except Exception as e:
            logger.error(f"OCR extraction with confidence failed: {str(e)}")
            raise OCRError(f"Failed to extract text with confidence: {str(e)}")
    
    def _build_tesseract_config(self, config: Optional[OCRConfig]) -> str:
        """Build Tesseract configuration string."""
        if config:
            return config.to_tesseract_config()
        return "--psm 8"  # Default: treat as single word


class EasyOCREngine(OCREngine):
    """OCR engine using EasyOCR (placeholder for future implementation)."""
    
    def __init__(self, preprocessor: Optional[ImagePreprocessor] = None):
        """Initialize EasyOCR engine."""
        self.preprocessor = preprocessor or BasicImagePreprocessor()
        logger.warning("EasyOCR engine is not yet implemented. Using Tesseract as fallback.")
        self._fallback_engine = TesseractOCREngine(preprocessor)
    
    def extract_text(self, image: Image.Image, config: Optional[OCRConfig] = None) -> str:
        """Extract text using EasyOCR (fallback to Tesseract)."""
        return self._fallback_engine.extract_text(image, config)
    
    def extract_text_with_confidence(self, image: Image.Image, 
                                   config: Optional[OCRConfig] = None) -> Tuple[str, float]:
        """Extract text with confidence using EasyOCR (fallback to Tesseract)."""
        return self._fallback_engine.extract_text_with_confidence(image, config)


class OCREngineFactory:
    """Factory for creating OCR engines."""
    
    _engines = {
        'tesseract': TesseractOCREngine,
        'easyocr': EasyOCREngine,
    }
    
    @classmethod
    def create_engine(cls, engine_type: str = 'tesseract', 
                     preprocessor: Optional[ImagePreprocessor] = None) -> OCREngine:
        """
        Create an OCR engine instance.
        
        Args:
            engine_type: Type of OCR engine ('tesseract', 'easyocr')
            preprocessor: Optional image preprocessor
            
        Returns:
            OCR engine instance
            
        Raises:
            ValueError: If engine type is not supported
        """
        if engine_type not in cls._engines:
            raise ValueError(f"Unsupported OCR engine: {engine_type}. "
                           f"Available engines: {list(cls._engines.keys())}")
        
        return cls._engines[engine_type](preprocessor)
    
    @classmethod
    def get_available_engines(cls) -> list[str]:
        """Get list of available OCR engines."""
        return list(cls._engines.keys())