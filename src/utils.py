"""Utility functions for the Number Plate Extractor"""

import json
from typing import List, Dict, Any
from tabulate import tabulate


def print_results_table(image_path: str, plates: List[Dict]) -> None:
    """
    Print results in a formatted table
    
    Args:
        image_path: Path to the processed image
        plates: List of extracted plates
    """
    print(f"\nImage: {image_path}")
    print("-" * 50)
    
    if not plates:
        print("No plates detected")
        return
    
    table_data = [
        [plate['text'], f"{plate['confidence']:.1f}%"]
        for plate in plates
    ]
    
    headers = ["Plate Number", "Confidence"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def print_results_json(image_path: str, plates: List[Dict], all_text: List[Dict] = None) -> str:
    """
    Return results as JSON string with plates and all detected text
    
    Args:
        image_path: Path to the processed image
        plates: List of extracted plates
        all_text: List of all detected text blocks
        
    Returns:
        JSON string representation of results
    """
    result = {
        "image": image_path,
        "plates": plates,
        "plate_count": len(plates),
        "all_detected_text": all_text if all_text else [],
        "total_text_blocks": len(all_text) if all_text else 0
    }
    return json.dumps(result, indent=2)


def print_batch_results_json(results: List[Dict]) -> str:
    """
    Return batch results as JSON string
    
    Args:
        results: List of result dictionaries
        
    Returns:
        JSON string representation of results
    """
    batch_result = {
        "total_images": len(results),
        "results": results
    }
    return json.dumps(batch_result, indent=2)


def normalize_confidence(confidence: float) -> float:
    """
    Normalize confidence value to 0-100 range
    
    Args:
        confidence: Confidence value (could be 0-1 or 0-100)
        
    Returns:
        Normalized confidence value in 0-100 range
    """
    if confidence > 1.0:
        return confidence
    return confidence * 100


def validate_confidence_threshold(threshold: float) -> bool:
    """
    Validate confidence threshold value
    
    Args:
        threshold: Confidence threshold value
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= threshold <= 100


def get_image_files(folder_path: str) -> List[str]:
    """
    Get all image files from a folder
    
    Args:
        folder_path: Path to the folder
        
    Returns:
        List of image file paths
    """
    import os
    from pathlib import Path
    
    if not os.path.isdir(folder_path):
        raise ValueError(f"Invalid folder path: {folder_path}")
    
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    image_files = []
    
    for filename in os.listdir(folder_path):
        file_ext = Path(filename).suffix.lower()
        if file_ext in supported_formats:
            full_path = os.path.join(folder_path, filename)
            if os.path.isfile(full_path):
                image_files.append(full_path)
    
    return sorted(image_files)


def format_error_message(error: Exception) -> str:
    """
    Format error message for display
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error message
    """
    return f"Error: {str(error)}"


def summarize_batch_results(results: List[Dict]) -> Dict[str, Any]:
    """
    Summarize batch processing results
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Summary statistics
    """
    total_images = len(results)
    total_plates = sum(len(r.get('plates', [])) for r in results)
    successful = sum(1 for r in results if r.get('success', False))
    failed = total_images - successful
    
    return {
        'total_images': total_images,
        'successful': successful,
        'failed': failed,
        'total_plates_detected': total_plates,
        'average_plates_per_image': total_plates / successful if successful > 0 else 0
    }
