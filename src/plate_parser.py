"""Plate number parser module for extracting number plates from Textract results"""

import re
from typing import List, Dict, Tuple, Optional


class PlateParser:
    """Parse and extract number plates from Textract responses"""
    
    # Common number plate patterns
    DEFAULT_PATTERNS = {
        'indian': r'^[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[A-Z]{1,2}[-\s]?[A-Z0-9]{4,5}$',  # MH 01 AB 1234 or NL01A J0044
        'international': r'^[A-Z0-9\-\s]{5,12}$',  # Generic international
        'us': r'^[A-Z]{1,3}[-\s]?[0-9]{3,4}[-\s]?[A-Z]{0,3}$',  # US format
        'uk': r'^[A-Z]{2}[0-9]{2}[-\s]?[A-Z]{3}$',  # UK format (simplified)
    }
    
    def __init__(self, confidence_threshold: float = 80.0, pattern: str = None):
        """
        Initialize plate parser
        
        Args:
            confidence_threshold: Minimum confidence percentage (0-100)
            pattern: Custom regex pattern for plate matching (defaults to Indian format)
        """
        self.confidence_threshold = confidence_threshold
        
        # Use custom pattern or default to Indian format
        if pattern:
            self.pattern = pattern
        else:
            self.pattern = self.DEFAULT_PATTERNS['indian']
        
        self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)
    
    @staticmethod
    def filter_by_confidence(blocks: List[Dict], threshold: float) -> List[Dict]:
        """
        Filter blocks by confidence threshold
        
        Args:
            blocks: List of text blocks from Textract
            threshold: Confidence threshold (0-100)
            
        Returns:
            Filtered list of blocks meeting confidence threshold
        """
        return [block for block in blocks if block.get('confidence', 0) >= threshold]
    
    @staticmethod
    def merge_adjacent_words(words: List[Dict]) -> List[str]:
        """
        Merge adjacent words to form potential license plate strings
        
        Args:
            words: List of word blocks with geometry information
            
        Returns:
            List of merged text strings
        """
        if not words:
            return []
        
        merged = []
        current_text = words[0].get('text', '')
        current_group = [words[0]]
        
        for i in range(1, len(words)):
            word = words[i]
            prev_word = current_group[-1]
            
            # Check if words are close to each other (horizontally adjacent)
            prev_geometry = prev_word.get('geometry', {})
            curr_geometry = word.get('geometry', {})
            
            # Get bounding box coordinates
            prev_right = prev_geometry.get('BoundingBox', {}).get('Left', 0) + prev_geometry.get('BoundingBox', {}).get('Width', 0)
            curr_left = curr_geometry.get('BoundingBox', {}).get('Left', 0)
            
            # If words are close, merge them
            if curr_left - prev_right < 0.02:  # Threshold for "close" words
                current_text += ' ' + word.get('text', '')
                current_group.append(word)
            else:
                # Words are far apart, start new group
                if current_text.strip():
                    merged.append(current_text.strip())
                current_text = word.get('text', '')
                current_group = [word]
        
        # Add the last group
        if current_text.strip():
            merged.append(current_text.strip())
        
        return merged
    
    def extract_plates(self, textract_blocks: List[Dict]) -> List[Dict]:
        """
        Extract number plates from Textract blocks
        
        Args:
            textract_blocks: List of text blocks from Textract response
            
        Returns:
            List of extracted plates with text and confidence
        """
        # Filter by confidence
        confident_blocks = self.filter_by_confidence(textract_blocks, self.confidence_threshold)
        
        if not confident_blocks:
            return []
        
        # Try matching individual blocks first (for single-word plates)
        plates = []
        plate_texts_found = set()
        
        for block in confident_blocks:
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # Check if text matches plate pattern
            if self.compiled_pattern.match(text):
                if text not in plate_texts_found:
                    plates.append({
                        'text': text,
                        'confidence': block.get('confidence', 0),
                        'block_type': 'single'
                    })
                    plate_texts_found.add(text)
        
        # Try merging adjacent words
        merged_texts = self.merge_adjacent_words(confident_blocks)
        for merged_text in merged_texts:
            if self.compiled_pattern.match(merged_text):
                if merged_text not in plate_texts_found:
                    # Calculate average confidence
                    avg_confidence = sum(
                        block.get('confidence', 0) 
                        for block in confident_blocks
                    ) / len(confident_blocks) if confident_blocks else 0
                    
                    plates.append({
                        'text': merged_text,
                        'confidence': avg_confidence,
                        'block_type': 'merged'
                    })
                    plate_texts_found.add(merged_text)
        
        # Try combining consecutive text blocks (for multi-line plates)
        for i in range(len(confident_blocks)):
            for j in range(i + 1, min(i + 4, len(confident_blocks))):  # Try combining up to 3 consecutive blocks
                combined_text = ' '.join(
                    block.get('text', '').strip() 
                    for block in confident_blocks[i:j+1]
                    if block.get('text', '').strip()
                )
                
                if combined_text and self.compiled_pattern.match(combined_text):
                    if combined_text not in plate_texts_found:
                        # Calculate average confidence from blocks used
                        blocks_used = confident_blocks[i:j+1]
                        avg_confidence = sum(
                            block.get('confidence', 0) 
                            for block in blocks_used
                        ) / len(blocks_used) if blocks_used else 0
                        
                        plates.append({
                            'text': combined_text,
                            'confidence': avg_confidence,
                            'block_type': 'multiline'
                        })
                        plate_texts_found.add(combined_text)
        
        # Sort by confidence descending
        plates.sort(key=lambda x: x['confidence'], reverse=True)
        
        return plates
    
    @staticmethod
    def format_plates(plates: List[Dict]) -> List[Dict]:
        """
        Format extracted plates for output
        
        Args:
            plates: List of extracted plates
            
        Returns:
            Formatted plates list
        """
        return [
            {
                'text': plate['text'],
                'confidence': round(plate['confidence'], 2)
            }
            for plate in plates
        ]
    
    @staticmethod
    def clean_plate_text(text: str) -> str:
        """
        Clean plate text by removing extra spaces and normalizing format
        
        Args:
            text: Raw plate text
            
        Returns:
            Cleaned plate text
        """
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        # Normalize hyphens
        text = text.replace('- ', '-').replace(' -', '-')
        return text
    
    @staticmethod
    def validate_plate(text: str) -> bool:
        """
        Basic validation for plate text
        
        Args:
            text: Plate text to validate
            
        Returns:
            True if text looks like a valid plate
        """
        # Remove spaces and hyphens for validation
        clean_text = text.replace(' ', '').replace('-', '')
        
        # Should be alphanumeric
        if not clean_text.isalnum():
            return False
        
        # Should have minimum and maximum length
        if len(clean_text) < 7 or len(clean_text) > 13:
            return False
        
        return True


def get_all_detected_text(textract_response: Dict) -> List[Dict]:
    """
    Extract all detected text from Textract response
    
    Args:
        textract_response: Formatted Textract response
        
    Returns:
        List of all detected text blocks with confidence scores
    """
    lines = textract_response.get('lines', [])
    
    all_text = [
        {
            'text': line.get('text', ''),
            'confidence': round(line.get('confidence', 0), 2)
        }
        for line in lines
        if line.get('text', '').strip()
    ]
    
    return all_text


def parse_plates_from_textract(
    textract_response: Dict,
    confidence_threshold: float = 80.0,
    pattern: str = None
) -> Dict:
    """
    Parse number plates and all text from a Textract response
    
    Args:
        textract_response: Formatted Textract response
        confidence_threshold: Minimum confidence percentage
        pattern: Custom regex pattern for plate matching
        
    Returns:
        Dictionary containing plates and all detected text
    """
    parser = PlateParser(
        confidence_threshold=confidence_threshold,
        pattern=pattern
    )
    
    # Get lines from formatted response
    lines = textract_response.get('lines', [])
    
    # Extract plates
    plates = parser.extract_plates(lines)
    
    # Format plates for output
    formatted_plates = parser.format_plates(plates)
    
    # Get all detected text
    all_text = get_all_detected_text(textract_response)
    
    return {
        'plates': formatted_plates,
        'all_detected_text': all_text
    }
