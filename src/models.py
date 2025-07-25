"""
Data models for the OCR String Validation Tool.

This module contains all the data structures used throughout the application,
implemented using dataclasses for better type safety and immutability.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum


class MatchResult(Enum):
    """Enumeration for validation results."""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    MISSING_IMAGE = "MISSING_IMAGE"
    MISSING_COORDINATES = "MISSING_COORDINATES"


@dataclass(frozen=True)
class Coordinate:
    """Represents a bounding box coordinate on an image."""
    left: int
    top: int
    right: int
    bottom: int
    
    @property
    def width(self) -> int:
        """Calculate the width of the bounding box."""
        return self.right - self.left
    
    @property
    def height(self) -> int:
        """Calculate the height of the bounding box."""
        return self.bottom - self.top
    
    @property
    def area(self) -> int:
        """Calculate the area of the bounding box."""
        return self.width * self.height
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to tuple format (left, top, right, bottom)."""
        return (self.left, self.top, self.right, self.bottom)
    
    def to_opencv_rect(self) -> Tuple[int, int, int, int]:
        """Convert to OpenCV rectangle format (x, y, width, height)."""
        return (self.left, self.top, self.width, self.height)


@dataclass(frozen=True)
class TestStep:
    """Represents a single test step from the protocol."""
    step_id: str
    screen_id: str
    expected_string_id: str
    
    @property
    def coordinate_key(self) -> Tuple[str, str, str]:
        """Generate a unique key for coordinate lookup."""
        return (self.step_id, self.screen_id, self.expected_string_id)


@dataclass
class ValidationResult:
    """Represents the result of a single validation operation."""
    step: TestStep
    expected_text: str
    ocr_output: str
    match_result: MatchResult
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if the validation was successful."""
        return self.match_result == MatchResult.PASS


@dataclass
class AnnotationData:
    """Represents annotation data for a string region."""
    step_id: str
    screen_id: str
    expected_string_id: str
    coordinate: Coordinate
    
    def to_csv_row(self) -> List[str]:
        """Convert to CSV row format."""
        return [
            self.step_id,
            self.screen_id,
            self.expected_string_id,
            str(self.coordinate.left),
            str(self.coordinate.top),
            str(self.coordinate.right),
            str(self.coordinate.bottom)
        ]


@dataclass
class ValidationConfig:
    """Configuration settings for the validation tool."""
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    language: str = "en-US"
    tesseract_config: str = ""
    fuzzy_matching_threshold: float = 0.8
    enable_preprocessing: bool = True
    log_level: str = "INFO"
    
    @property
    def protocol_file(self) -> Path:
        """Path to the test protocol CSV file."""
        return self.data_dir / "test_protocol.csv"
    
    @property
    def string_map_file(self) -> Path:
        """Path to the expected strings JSON file."""
        return self.data_dir / "expected_strings" / f"{self.language}.json"
    
    @property
    def screenshot_dir(self) -> Path:
        """Path to the screenshots directory."""
        return self.data_dir / "screenshots"
    
    @property
    def coordinate_file(self) -> Path:
        """Path to the string coordinates CSV file."""
        return self.data_dir / "string_coordinates.csv"
    
    @property
    def results_file(self) -> Path:
        """Path to the results CSV file."""
        return self.output_dir / f"results-{self.language}.csv"
    
    def __post_init__(self):
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class OCRConfig:
    """Configuration for OCR processing."""
    language: str = "eng"
    config: str = "--psm 8"  # Treat as single word
    preprocessing_enabled: bool = True
    dpi: int = 300
    
    def to_tesseract_config(self) -> str:
        """Convert to tesseract configuration string."""
        return f"{self.config} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "