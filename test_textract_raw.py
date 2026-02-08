#!/usr/bin/env python3
"""
Test script to view raw AWS Textract API response without any postprocessing

This script sends an image to Textract and displays the complete raw response
with all blocks and metadata for debugging and analysis purposes.
"""

import sys
import os
import json
import argparse
from pprint import pprint

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from image_preprocessor import preprocess_image, ImagePreprocessor
from textract_client import get_textract_client


def display_raw_response(image_path: str, enhance: bool = True, output_file: str = None):
    """
    Send image to Textract and display raw API response
    
    Args:
        image_path: Path to the image file
        enhance: Whether to enhance the image
        output_file: Optional file path to save the response
    """
    print("=" * 80)
    print("AWS TEXTRACT RAW API RESPONSE TEST")
    print("=" * 80)
    print(f"\nImage: {image_path}")
    print(f"Enhancement: {'Enabled' if enhance else 'Disabled'}")
    print()
    
    try:
        # Validate image
        is_valid, error_msg = ImagePreprocessor.validate_image_file(image_path)
        if not is_valid:
            print(f"❌ Validation Error: {error_msg}")
            return
        
        print("✓ Image validation passed")
        
        # Preprocess image
        print("Processing image...")
        image_bytes = preprocess_image(image_path, enhance=enhance)
        print(f"✓ Image preprocessed ({len(image_bytes) / 1024:.2f} KB)")
        
        # Call Textract API
        print("\nCalling Textract API...")
        textract = get_textract_client()
        response = textract.detect_document_text(image_bytes)
        print("✓ Textract API call successful")
        
        # Display response statistics
        blocks = response.get('Blocks', [])
        print(f"\n📊 Response Statistics:")
        print(f"  - Total Blocks: {len(blocks)}")
        
        block_types = {}
        for block in blocks:
            block_type = block.get('BlockType', 'UNKNOWN')
            block_types[block_type] = block_types.get(block_type, 0) + 1
        
        for block_type, count in sorted(block_types.items()):
            print(f"    - {block_type}: {count}")
        
        # Display metadata
        print(f"\n📝 Document Metadata:")
        print(f"  - ResponseMetadata: {response.get('ResponseMetadata', {})}")
        
        # Display full raw response
        print("\n" + "=" * 80)
        print("FULL RAW RESPONSE:")
        print("=" * 80 + "\n")
        pprint(response, width=100)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, default=str)
            print(f"\n✓ Response saved to: {output_file}")
        
        # Display individual blocks in detail
        print("\n" + "=" * 80)
        print("DETAILED BLOCK BREAKDOWN:")
        print("=" * 80 + "\n")
        
        for idx, block in enumerate(blocks):
            print(f"\n--- Block {idx} ---")
            print(f"Type: {block.get('BlockType')}")
            print(f"Text: {block.get('Text', 'N/A')}")
            print(f"Confidence: {block.get('Confidence', 'N/A')}")
            print(f"Geometry: {block.get('Geometry', {})}")
            if 'Relationships' in block:
                print(f"Relationships: {block.get('Relationships')}")
    
    except ValueError as e:
        print(f"❌ Validation Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='View raw AWS Textract API response for debugging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View raw response for a single image
  python test_textract_raw.py --image vehicle/444R104022602182_vehicle.jpg
  
  # View response without image enhancement
  python test_textract_raw.py --image car.jpg --no-enhance
  
  # Save raw response to JSON file
  python test_textract_raw.py --image car.jpg --output raw_response.json
        """
    )
    
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Path to the image file'
    )
    parser.add_argument(
        '--no-enhance',
        action='store_true',
        help='Disable image enhancement preprocessing'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Save raw response to JSON file'
    )
    
    args = parser.parse_args()
    
    display_raw_response(
        image_path=args.image,
        enhance=not args.no_enhance,
        output_file=args.output
    )


if __name__ == '__main__':
    main()
