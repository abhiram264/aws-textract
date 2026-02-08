"""Image preprocessing module for AWS Textract Number Plate Extractor"""

import os
from pathlib import Path
from typing import Tuple
from PIL import Image
import cv2
import numpy as np


class ImagePreprocessor:
    """Handles image loading, validation, and preprocessing"""
    
    # Maximum file size for Textract (5 MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    
    def __init__(self):
        pass
    
    @staticmethod
    def validate_image_file(image_path: str) -> Tuple[bool, str]:
        """
        Validate image file existence, format, and size
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(image_path):
            return False, f"File not found: {image_path}"
        
        if not os.path.isfile(image_path):
            return False, f"Path is not a file: {image_path}"
        
        # Check file extension
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in ImagePreprocessor.SUPPORTED_FORMATS:
            return False, f"Unsupported format: {file_ext}. Supported: {', '.join(ImagePreprocessor.SUPPORTED_FORMATS)}"
        
        # Check file size
        file_size = os.path.getsize(image_path)
        if file_size > ImagePreprocessor.MAX_FILE_SIZE:
            return False, f"File size {file_size / (1024*1024):.2f} MB exceeds maximum {ImagePreprocessor.MAX_FILE_SIZE / (1024*1024)} MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, ""
    
    @staticmethod
    def load_image_as_bytes(image_path: str) -> bytes:
        """
        Load image file as bytes
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image file as bytes
            
        Raises:
            IOError: If file cannot be read
        """
        try:
            with open(image_path, 'rb') as f:
                return f.read()
        except IOError as e:
            raise IOError(f"Failed to read image file {image_path}: {str(e)}")
    
    @staticmethod
    def load_image_with_pillow(image_path: str) -> Image.Image:
        """
        Load image using Pillow for manipulation
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object
            
        Raises:
            IOError: If image cannot be opened
        """
        try:
            img = Image.open(image_path)
            return img
        except Exception as e:
            raise IOError(f"Failed to open image {image_path}: {str(e)}")
    
    @staticmethod
    def load_image_with_opencv(image_path: str) -> np.ndarray:
        """
        Load image using OpenCV for advanced processing
        
        Args:
            image_path: Path to the image file
            
        Returns:
            OpenCV image as numpy array (BGR format)
            
        Raises:
            IOError: If image cannot be loaded
        """
        img = cv2.imread(image_path)
        if img is None:
            raise IOError(f"Failed to load image with OpenCV: {image_path}")
        return img
    
    @staticmethod
    def crop_roi(image_cv: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Crop Region of Interest (ROI) from image
        
        Args:
            image_cv: OpenCV image as numpy array
            roi: Tuple of (x, y, width, height) for the region
            
        Returns:
            Cropped image
        """
        x, y, w, h = roi
        return image_cv[y:y+h, x:x+w]
    
    @staticmethod
    def enhance_contrast(image_cv: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            image_cv: OpenCV image as numpy array
            
        Returns:
            Enhanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge channels back
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    @staticmethod
    def convert_to_grayscale(image_cv: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale
        
        Args:
            image_cv: OpenCV image as numpy array (BGR format)
            
        Returns:
            Grayscale image
        """
        return cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    @staticmethod
    def apply_bilateral_filter(image_cv: np.ndarray) -> np.ndarray:
        """
        Apply bilateral filter to reduce noise while preserving edges
        
        Args:
            image_cv: OpenCV image as numpy array
            
        Returns:
            Filtered image
        """
        return cv2.bilateralFilter(image_cv, 9, 75, 75)
    
    @staticmethod
    def save_preprocessed_image(image_cv: np.ndarray, output_path: str) -> None:
        """
        Save preprocessed image to disk
        
        Args:
            image_cv: OpenCV image as numpy array
            output_path: Path where to save the image
        """
        success = cv2.imwrite(output_path, image_cv)
        if not success:
            raise IOError(f"Failed to save image to {output_path}")
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> Tuple[int, int]:
        """
        Get image dimensions (width, height)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height)
        """
        img = ImagePreprocessor.load_image_with_pillow(image_path)
        return img.size


def preprocess_image(image_path: str, enhance: bool = True) -> bytes:
    """
    Preprocess an image and return as bytes for Textract
    
    Args:
        image_path: Path to the image file
        enhance: Whether to enhance the image for better OCR results
        
    Returns:
        Preprocessed image as bytes
        
    Raises:
        ValueError: If image validation fails
        IOError: If image processing fails
    """
    # Validate image
    is_valid, error_msg = ImagePreprocessor.validate_image_file(image_path)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Load and enhance if requested
    if enhance:
        img_cv = ImagePreprocessor.load_image_with_opencv(image_path)
        
        # Apply enhancements
        img_cv = ImagePreprocessor.apply_bilateral_filter(img_cv)
        img_cv = ImagePreprocessor.enhance_contrast(img_cv)
        
        # Convert enhanced image back to bytes using Pillow
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        import io
        img_bytes = io.BytesIO()
        img_pil.save(img_bytes, format='JPEG', quality=95)
        return img_bytes.getvalue()
    else:
        # Load raw image bytes
        return ImagePreprocessor.load_image_as_bytes(image_path)
