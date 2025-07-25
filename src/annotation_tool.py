"""
Interactive annotation tool for the String Validation Tool.

This module provides a GUI-based tool for annotating string regions
in screenshots using OpenCV.
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np

from .models import AnnotationData, Coordinate, ValidationConfig
from .exceptions import AnnotationError

logger = logging.getLogger(__name__)


class AnnotationTool:
    """
    Interactive tool for annotating string regions in screenshots.
    
    This class provides a GUI interface using OpenCV for selecting
    regions of interest and associating them with expected string IDs.
    """
    
    def __init__(self, config: ValidationConfig):
        """
        Initialize the annotation tool.
        
        Args:
            config: Validation configuration
        """
        self.config = config
        self.annotations: List[AnnotationData] = []
        
        # Ensure screenshot directory exists
        if not self.config.screenshot_dir.exists():
            raise AnnotationError(
                f"Screenshot directory not found: {self.config.screenshot_dir}"
            )
    
    def run_annotation_session(self) -> List[AnnotationData]:
        """
        Run an interactive annotation session for all screenshots.
        
        Returns:
            List of annotation data
            
        Raises:
            AnnotationError: If annotation fails
        """
        try:
            # Get all image files
            image_files = self._get_image_files()
            if not image_files:
                raise AnnotationError("No image files found in screenshot directory")
            
            logger.info(f"Found {len(image_files)} images to annotate")
            
            # Process each image
            for img_path in image_files:
                try:
                    self._annotate_image(img_path)
                except KeyboardInterrupt:
                    logger.info("Annotation session interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Error annotating {img_path.name}: {str(e)}")
                    continue
            
            # Save annotations
            if self.annotations:
                self._save_annotations()
                logger.info(f"Saved {len(self.annotations)} annotations")
            
            return self.annotations
            
        except Exception as e:
            raise AnnotationError(f"Annotation session failed: {str(e)}")
    
    def _get_image_files(self) -> List[Path]:
        """Get list of image files in the screenshot directory."""
        extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        image_files = []
        
        for ext in extensions:
            image_files.extend(self.config.screenshot_dir.glob(f"*{ext}"))
            image_files.extend(self.config.screenshot_dir.glob(f"*{ext.upper()}"))
        
        return sorted(image_files)
    
    def _annotate_image(self, image_path: Path) -> None:
        """
        Annotate a single image.
        
        Args:
            image_path: Path to the image file
        """
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise AnnotationError(f"Failed to load image: {image_path}")
            
            screen_id = image_path.stem
            logger.info(f"Annotating image: {screen_id}")
            
            # Get step ID from user
            step_id = self._get_step_id_input(screen_id)
            if not step_id:
                logger.info(f"Skipping image {screen_id} (no step ID provided)")
                return
            
            # Annotate regions
            while True:
                try:
                    annotation = self._annotate_region(image, step_id, screen_id)
                    if annotation:
                        self.annotations.append(annotation)
                        logger.info(f"Added annotation: {annotation.expected_string_id}")
                    else:
                        break  # User chose to stop annotating this image
                        
                except Exception as e:
                    logger.error(f"Error during region annotation: {str(e)}")
                    break
            
        except Exception as e:
            raise AnnotationError(f"Failed to annotate image {image_path}: {str(e)}", screen_id)
    
    def _get_step_id_input(self, screen_id: str) -> Optional[str]:
        """
        Get step ID input from user.
        
        Args:
            screen_id: Screen identifier
            
        Returns:
            Step ID or None if user cancels
        """
        print(f"\n=== Annotating Screen: {screen_id} ===")
        while True:
            try:
                step_id = input("Enter Step ID for this image (or 'skip' to skip): ").strip()
                
                if step_id.lower() == 'skip':
                    return None
                
                if step_id:
                    return step_id
                
                print("Step ID cannot be empty. Please try again.")
                
            except (KeyboardInterrupt, EOFError):
                return None
    
    def _annotate_region(self, image: np.ndarray, step_id: str, screen_id: str) -> Optional[AnnotationData]:
        """
        Annotate a single region in the image.
        
        Args:
            image: OpenCV image array
            step_id: Step identifier
            screen_id: Screen identifier
            
        Returns:
            Annotation data or None if user cancels
        """
        try:
            # Create window
            window_name = f"Annotate: {screen_id}"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
            # Show instruction
            print("\nInstructions:")
            print("1. Click and drag to select a region")
            print("2. Press ENTER to confirm selection")
            print("3. Press ESC to skip this region")
            print("4. Press 'q' to finish annotating this image")
            
            # Select ROI
            roi = cv2.selectROI(
                window_name, 
                image, 
                fromCenter=False, 
                showCrosshair=True
            )
            
            # Clean up window
            cv2.destroyWindow(window_name)
            
            # Check if user cancelled
            if sum(roi) == 0:
                print("No region selected.")
                return None
            
            # Convert ROI to coordinate
            x, y, w, h = roi
            coordinate = Coordinate(
                left=x,
                top=y,
                right=x + w,
                bottom=y + h
            )
            
            print(f"Selected region: {coordinate.to_tuple()}")
            
            # Get expected string ID
            expected_string_id = self._get_string_id_input()
            if not expected_string_id:
                return None
            
            # Create annotation data
            annotation = AnnotationData(
                step_id=step_id,
                screen_id=screen_id,
                expected_string_id=expected_string_id,
                coordinate=coordinate
            )
            
            return annotation
            
        except Exception as e:
            logger.error(f"Error during region annotation: {str(e)}")
            return None
    
    def _get_string_id_input(self) -> Optional[str]:
        """
        Get expected string ID input from user.
        
        Returns:
            Expected string ID or None if user cancels
        """
        while True:
            try:
                string_id = input("Enter Expected String ID for this region (or 'cancel' to cancel): ").strip()
                
                if string_id.lower() == 'cancel':
                    return None
                
                if string_id:
                    return string_id
                
                print("Expected String ID cannot be empty. Please try again.")
                
            except (KeyboardInterrupt, EOFError):
                return None
    
    def _save_annotations(self) -> None:
        """Save annotations to CSV file."""
        try:
            with open(self.config.coordinate_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "StepID", "ScreenID", "ExpectedStringID", 
                    "Left", "Top", "Right", "Bottom"
                ])
                
                # Write annotation data
                for annotation in self.annotations:
                    writer.writerow(annotation.to_csv_row())
            
            logger.info(f"Annotations saved to {self.config.coordinate_file}")
            
        except Exception as e:
            raise AnnotationError(f"Failed to save annotations: {str(e)}")
    
    def load_existing_annotations(self) -> List[AnnotationData]:
        """
        Load existing annotations from file.
        
        Returns:
            List of existing annotation data
        """
        if not self.config.coordinate_file.exists():
            return []
        
        try:
            annotations = []
            with open(self.config.coordinate_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        coordinate = Coordinate(
                            left=int(row['Left']),
                            top=int(row['Top']),
                            right=int(row['Right']),
                            bottom=int(row['Bottom'])
                        )
                        
                        annotation = AnnotationData(
                            step_id=row['StepID'],
                            screen_id=row['ScreenID'],
                            expected_string_id=row['ExpectedStringID'],
                            coordinate=coordinate
                        )
                        
                        annotations.append(annotation)
                        
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid annotation row: {str(e)}")
                        continue
            
            logger.info(f"Loaded {len(annotations)} existing annotations")
            return annotations
            
        except Exception as e:
            logger.error(f"Failed to load existing annotations: {str(e)}")
            return []
    
    def preview_annotations(self, annotations: Optional[List[AnnotationData]] = None) -> None:
        """
        Preview annotations on images.
        
        Args:
            annotations: List of annotations to preview (uses self.annotations if None)
        """
        annotations_to_preview = annotations or self.annotations
        if not annotations_to_preview:
            logger.info("No annotations to preview")
            return
        
        # Group annotations by screen
        annotations_by_screen = {}
        for annotation in annotations_to_preview:
            if annotation.screen_id not in annotations_by_screen:
                annotations_by_screen[annotation.screen_id] = []
            annotations_by_screen[annotation.screen_id].append(annotation)
        
        # Preview each screen
        for screen_id, screen_annotations in annotations_by_screen.items():
            try:
                self._preview_screen_annotations(screen_id, screen_annotations)
            except Exception as e:
                logger.error(f"Error previewing annotations for {screen_id}: {str(e)}")
    
    def _preview_screen_annotations(self, screen_id: str, annotations: List[AnnotationData]) -> None:
        """
        Preview annotations for a single screen.
        
        Args:
            screen_id: Screen identifier
            annotations: List of annotations for this screen
        """
        # Load image
        image_path = self.config.screenshot_dir / f"{screen_id}.png"
        if not image_path.exists():
            logger.warning(f"Image not found for preview: {image_path}")
            return
        
        image = cv2.imread(str(image_path))
        if image is None:
            logger.warning(f"Failed to load image for preview: {image_path}")
            return
        
        # Draw annotations
        preview_image = image.copy()
        for i, annotation in enumerate(annotations):
            coord = annotation.coordinate
            
            # Draw rectangle
            cv2.rectangle(
                preview_image,
                (coord.left, coord.top),
                (coord.right, coord.bottom),
                (0, 255, 0),  # Green color
                2
            )
            
            # Add label
            label = f"{i+1}: {annotation.expected_string_id}"
            cv2.putText(
                preview_image,
                label,
                (coord.left, coord.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
        
        # Show preview
        window_name = f"Preview: {screen_id}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, preview_image)
        
        print(f"\nPreviewing {len(annotations)} annotations for {screen_id}")
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyWindow(window_name)