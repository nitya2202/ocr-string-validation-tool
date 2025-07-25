"""
Data loading implementations for the String Validation Tool.

This module provides concrete implementations for loading various data formats
including CSV files and JSON mappings.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from .interfaces import DataLoader
from .models import TestStep, Coordinate
from .exceptions import DataLoadError

logger = logging.getLogger(__name__)


class CSVDataLoader(DataLoader):
    """Data loader for CSV files."""
    
    def load_test_protocol(self, file_path: str) -> List[TestStep]:
        """
        Load test protocol from CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            List of TestStep objects
            
        Raises:
            DataLoadError: If file loading fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataLoadError(f"Protocol file not found: {file_path}", file_path)
            
            steps = []
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validate required columns
                required_columns = {'StepID', 'ScreenID', 'ExpectedStringID'}
                if not required_columns.issubset(reader.fieldnames or []):
                    missing_cols = required_columns - set(reader.fieldnames or [])
                    raise DataLoadError(
                        f"Missing required columns in protocol file: {missing_cols}",
                        file_path
                    )
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        # Validate row data
                        if not all(row.get(col, '').strip() for col in required_columns):
                            logger.warning(f"Skipping row {row_num}: missing required data")
                            continue
                        
                        step = TestStep(
                            step_id=row['StepID'].strip(),
                            screen_id=row['ScreenID'].strip(),
                            expected_string_id=row['ExpectedStringID'].strip()
                        )
                        steps.append(step)
                        
                    except Exception as e:
                        logger.error(f"Error parsing row {row_num}: {str(e)}")
                        continue
            
            if not steps:
                raise DataLoadError("No valid test steps found in protocol file", file_path)
            
            logger.info(f"Loaded {len(steps)} test steps from {file_path}")
            return steps
            
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load test protocol: {str(e)}", file_path)
    
    def load_expected_strings(self, file_path: str) -> Dict[str, str]:
        """
        Load expected strings mapping from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary mapping string IDs to expected text
            
        Raises:
            DataLoadError: If file loading fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataLoadError(f"Expected strings file not found: {file_path}", file_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise DataLoadError("Expected strings file must contain a JSON object", file_path)
            
            # Validate that all values are strings
            invalid_entries = [(k, v) for k, v in data.items() if not isinstance(v, str)]
            if invalid_entries:
                logger.warning(f"Found non-string values in expected strings: {invalid_entries}")
                # Convert to strings
                for k, v in invalid_entries:
                    data[k] = str(v)
            
            logger.info(f"Loaded {len(data)} expected strings from {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in expected strings file: {str(e)}", file_path)
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load expected strings: {str(e)}", file_path)
    
    def load_coordinates(self, file_path: str) -> Dict[Tuple[str, str, str], Coordinate]:
        """
        Load coordinate mappings from CSV file.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary mapping (step_id, screen_id, string_id) to Coordinate
            
        Raises:
            DataLoadError: If file loading fails
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataLoadError(f"Coordinates file not found: {file_path}", file_path)
            
            coordinates = {}
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validate required columns
                required_columns = {
                    'StepID', 'ScreenID', 'ExpectedStringID',
                    'Left', 'Top', 'Right', 'Bottom'
                }
                if not required_columns.issubset(reader.fieldnames or []):
                    missing_cols = required_columns - set(reader.fieldnames or [])
                    raise DataLoadError(
                        f"Missing required columns in coordinates file: {missing_cols}",
                        file_path
                    )
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        # Validate row data
                        if not all(row.get(col, '').strip() for col in required_columns):
                            logger.warning(f"Skipping row {row_num}: missing required data")
                            continue
                        
                        # Parse coordinate values
                        try:
                            left = int(row['Left'])
                            top = int(row['Top'])
                            right = int(row['Right'])
                            bottom = int(row['Bottom'])
                        except ValueError as e:
                            logger.error(f"Invalid coordinate values in row {row_num}: {str(e)}")
                            continue
                        
                        # Validate coordinate bounds
                        if left >= right or top >= bottom:
                            logger.error(f"Invalid coordinate bounds in row {row_num}: "
                                       f"({left}, {top}, {right}, {bottom})")
                            continue
                        
                        if any(coord < 0 for coord in [left, top, right, bottom]):
                            logger.error(f"Negative coordinates in row {row_num}: "
                                       f"({left}, {top}, {right}, {bottom})")
                            continue
                        
                        coordinate = Coordinate(left, top, right, bottom)
                        key = (
                            row['StepID'].strip(),
                            row['ScreenID'].strip(),
                            row['ExpectedStringID'].strip()
                        )
                        
                        if key in coordinates:
                            logger.warning(f"Duplicate coordinate entry for {key}, using latest")
                        
                        coordinates[key] = coordinate
                        
                    except Exception as e:
                        logger.error(f"Error parsing row {row_num}: {str(e)}")
                        continue
            
            if not coordinates:
                raise DataLoadError("No valid coordinates found in file", file_path)
            
            logger.info(f"Loaded {len(coordinates)} coordinate mappings from {file_path}")
            return coordinates
            
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load coordinates: {str(e)}", file_path)


class JSONDataLoader(DataLoader):
    """Data loader for JSON files (alternative implementation)."""
    
    def load_test_protocol(self, file_path: str) -> List[TestStep]:
        """
        Load test protocol from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of TestStep objects
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataLoadError(f"Protocol file not found: {file_path}", file_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise DataLoadError("JSON protocol file must contain an array of steps", file_path)
            
            steps = []
            for i, step_data in enumerate(data):
                try:
                    if not isinstance(step_data, dict):
                        logger.warning(f"Skipping invalid step at index {i}: not an object")
                        continue
                    
                    required_fields = ['step_id', 'screen_id', 'expected_string_id']
                    if not all(field in step_data for field in required_fields):
                        logger.warning(f"Skipping step at index {i}: missing required fields")
                        continue
                    
                    step = TestStep(
                        step_id=str(step_data['step_id']).strip(),
                        screen_id=str(step_data['screen_id']).strip(),
                        expected_string_id=str(step_data['expected_string_id']).strip()
                    )
                    steps.append(step)
                    
                except Exception as e:
                    logger.error(f"Error parsing step at index {i}: {str(e)}")
                    continue
            
            if not steps:
                raise DataLoadError("No valid test steps found in protocol file", file_path)
            
            logger.info(f"Loaded {len(steps)} test steps from {file_path}")
            return steps
            
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in protocol file: {str(e)}", file_path)
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load test protocol: {str(e)}", file_path)
    
    def load_expected_strings(self, file_path: str) -> Dict[str, str]:
        """Load expected strings mapping from JSON file (same as CSVDataLoader)."""
        csv_loader = CSVDataLoader()
        return csv_loader.load_expected_strings(file_path)
    
    def load_coordinates(self, file_path: str) -> Dict[Tuple[str, str, str], Coordinate]:
        """
        Load coordinate mappings from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary mapping (step_id, screen_id, string_id) to Coordinate
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise DataLoadError(f"Coordinates file not found: {file_path}", file_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise DataLoadError("JSON coordinates file must contain an array", file_path)
            
            coordinates = {}
            for i, coord_data in enumerate(data):
                try:
                    if not isinstance(coord_data, dict):
                        logger.warning(f"Skipping invalid coordinate at index {i}: not an object")
                        continue
                    
                    required_fields = [
                        'step_id', 'screen_id', 'expected_string_id',
                        'left', 'top', 'right', 'bottom'
                    ]
                    if not all(field in coord_data for field in required_fields):
                        logger.warning(f"Skipping coordinate at index {i}: missing required fields")
                        continue
                    
                    # Parse coordinate values
                    try:
                        left = int(coord_data['left'])
                        top = int(coord_data['top'])
                        right = int(coord_data['right'])
                        bottom = int(coord_data['bottom'])
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid coordinate values at index {i}: {str(e)}")
                        continue
                    
                    # Validate coordinate bounds
                    if left >= right or top >= bottom:
                        logger.error(f"Invalid coordinate bounds at index {i}: "
                                   f"({left}, {top}, {right}, {bottom})")
                        continue
                    
                    if any(coord < 0 for coord in [left, top, right, bottom]):
                        logger.error(f"Negative coordinates at index {i}: "
                                   f"({left}, {top}, {right}, {bottom})")
                        continue
                    
                    coordinate = Coordinate(left, top, right, bottom)
                    key = (
                        str(coord_data['step_id']).strip(),
                        str(coord_data['screen_id']).strip(),
                        str(coord_data['expected_string_id']).strip()
                    )
                    
                    if key in coordinates:
                        logger.warning(f"Duplicate coordinate entry for {key}, using latest")
                    
                    coordinates[key] = coordinate
                    
                except Exception as e:
                    logger.error(f"Error parsing coordinate at index {i}: {str(e)}")
                    continue
            
            if not coordinates:
                raise DataLoadError("No valid coordinates found in file", file_path)
            
            logger.info(f"Loaded {len(coordinates)} coordinate mappings from {file_path}")
            return coordinates
            
        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in coordinates file: {str(e)}", file_path)
        except DataLoadError:
            raise
        except Exception as e:
            raise DataLoadError(f"Failed to load coordinates: {str(e)}", file_path)


class DataLoaderFactory:
    """Factory for creating data loaders."""
    
    _loaders = {
        'csv': CSVDataLoader,
        'json': JSONDataLoader,
    }
    
    @classmethod
    def create_loader(cls, loader_type: str = 'csv') -> DataLoader:
        """
        Create a data loader instance.
        
        Args:
            loader_type: Type of data loader ('csv', 'json')
            
        Returns:
            Data loader instance
            
        Raises:
            ValueError: If loader type is not supported
        """
        if loader_type not in cls._loaders:
            raise ValueError(f"Unsupported loader type: {loader_type}. "
                           f"Available loaders: {list(cls._loaders.keys())}")
        
        return cls._loaders[loader_type]()
    
    @classmethod
    def get_available_loaders(cls) -> List[str]:
        """Get list of available loader types."""
        return list(cls._loaders.keys())