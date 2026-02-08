#!/usr/bin/env python3
"""
AWS Textract Number Plate Extractor - CLI Entry Point

Extract number plates from vehicle images using AWS Textract API.
"""

import argparse
import sys
import os
from typing import List, Dict, Any
import json

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_preprocessor import preprocess_image, ImagePreprocessor
from textract_client import get_textract_client, TextractClient
from plate_parser import parse_plates_from_textract
from utils import (
    print_results_table,
    print_results_json,
    print_batch_results_json,
    validate_confidence_threshold,
    get_image_files,
    format_error_message,
    summarize_batch_results,
    export_to_csv,
    export_to_csv_single
)


class NumberPlateExtractor:
    """Main application class for number plate extraction"""
    
    def __init__(self, confidence: float = 60.0, pattern: str = None, region: str = None):
        """
        Initialize the extractor
        
        Args:
            confidence: Confidence threshold (0-100)
            pattern: Custom regex pattern for plate matching
            region: AWS region
        """
        if not validate_confidence_threshold(confidence):
            raise ValueError(f"Confidence threshold must be between 0 and 100, got {confidence}")
        
        self.confidence = confidence
        self.pattern = pattern
        self.region = region
        
        # Initialize Textract client
        try:
            self.textract = get_textract_client(region=self.region)
        except Exception as e:
            print(f"Failed to initialize Textract client: {str(e)}", file=sys.stderr)
            sys.exit(1)
    
    def process_image(self, image_path: str, enhance: bool = True) -> Dict[str, Any]:
        """
        Process a single image and extract number plates
        
        Args:
            image_path: Path to the image file
            enhance: Whether to enhance the image
            
        Returns:
            Dictionary with extraction results
        """
        result = {
            'image': image_path,
            'success': False,
            'plates': [],
            'all_detected_text': [],
            'error': None
        }
        
        try:
            # Validate image
            is_valid, error_msg = ImagePreprocessor.validate_image_file(image_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            print(f"Processing: {image_path}")
            
            # Preprocess image
            image_bytes = preprocess_image(image_path, enhance=enhance)
            
            # Detect text with Textract
            print(f"  - Calling Textract API...")
            response = self.textract.detect_document_text(image_bytes)
            
            # Format response
            formatted_response = TextractClient.format_response(response)
            
            # Parse plates and get all detected text
            parse_result = parse_plates_from_textract(
                formatted_response,
                confidence_threshold=self.confidence,
                pattern=self.pattern
            )
            
            result['plates'] = parse_result['plates']
            result['all_detected_text'] = parse_result['all_detected_text']
            result['success'] = True
            
            if parse_result['plates']:
                print(f"  - Found {len(parse_result['plates'])} plate(s)")
            else:
                print(f"  - No plates detected")
            
            print(f"  - Total text detected: {len(parse_result['all_detected_text'])} blocks")
            
        except ValueError as e:
            result['error'] = str(e)
            print(f"  - Validation Error: {str(e)}", file=sys.stderr)
        except Exception as e:
            result['error'] = str(e)
            print(f"  - Error: {str(e)}", file=sys.stderr)
        
        return result
    
    def process_folder(self, folder_path: str, enhance: bool = True) -> List[Dict[str, Any]]:
        """
        Process all images in a folder
        
        Args:
            folder_path: Path to the folder
            enhance: Whether to enhance images
            
        Returns:
            List of results for each image
        """
        try:
            image_files = get_image_files(folder_path)
        except ValueError as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        
        if not image_files:
            print(f"No image files found in {folder_path}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Found {len(image_files)} image(s) to process\n")
        
        results = []
        for image_path in image_files:
            result = self.process_image(image_path, enhance=enhance)
            results.append(result)
        
        return results
    
    def process_single_image(self, image_path: str, enhance: bool = True) -> Dict[str, Any]:
        """
        Process a single image
        
        Args:
            image_path: Path to the image file
            enhance: Whether to enhance the image
            
        Returns:
            Result dictionary
        """
        return self.process_image(image_path, enhance=enhance)


def main():
    """Main entry point for CLI"""
    
    parser = argparse.ArgumentParser(
        description='Extract number plates from vehicle images using AWS Textract',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single image
  python main.py --image car.jpg
  
  # Process a folder of images
  python main.py --folder ./images
  
  # Set confidence threshold
  python main.py --image car.jpg --confidence 90
  
  # Output as JSON
  python main.py --folder ./images --json
  
  # Use custom plate pattern
  python main.py --image car.jpg --pattern "^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"
        """
    )
    
    # Mode selection (single image or folder)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--image',
        type=str,
        help='Path to a single image file'
    )
    mode_group.add_argument(
        '--folder',
        type=str,
        help='Path to a folder containing multiple images'
    )
    
    # Optional arguments
    parser.add_argument(
        '--confidence',
        type=float,
        default=60.0,
        help='Confidence threshold for plate detection (0-100, default: 60)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default=None,
        help='Custom regex pattern for plate matching (optional)'
    )
    parser.add_argument(
        '--region',
        type=str,
        default=None,
        help='AWS region (default: AWS_REGION env var or us-east-1)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Output results as CSV file'
    )
    parser.add_argument(
        '--include-low-confidence',
        action='store_true',
        help='Include number plates with confidence between 30-80%'
    )
    parser.add_argument(
        '--low-confidence-threshold',
        type=float,
        default=30.0,
        help='Minimum confidence threshold for low confidence plates (default: 30)'
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
        help='Save results to a file (optional)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = NumberPlateExtractor(
            confidence=args.confidence,
            pattern=args.pattern,
            region=args.region
        )
        
        # Process images
        if args.image:
            # Single image mode
            result = extractor.process_single_image(args.image, enhance=not args.no_enhance)
            
            if args.csv:
                # CSV output
                csv_output = args.output if args.output else 'results.csv'
                export_to_csv_single(
                    args.image,
                    result.get('all_detected_text', []),
                    result['plates'],
                    csv_output
                )
                print(f"Results saved to {csv_output}")
            elif args.json:
                output = print_results_json(args.image, result['plates'], result.get('all_detected_text', []))
                print(output)
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"\nResults saved to {args.output}")
            else:
                print_results_table(args.image, result['plates'])
                if args.output:
                    export_to_csv_single(
                        args.image,
                        result.get('all_detected_text', []),
                        result['plates'],
                        args.output
                    )
                    print(f"\nResults saved to {args.output}")
            
            # Exit with error if processing failed
            sys.exit(0 if result['success'] else 1)
        
        else:  # args.folder
            # Batch mode
            results = extractor.process_folder(args.folder, enhance=not args.no_enhance)
            
            print("\n" + "="*50)
            print("BATCH PROCESSING COMPLETE")
            print("="*50)
            
            # Display summary
            summary = summarize_batch_results(results)
            print(f"\nSummary:")
            print(f"  Total Images: {summary['total_images']}")
            print(f"  Successful: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Total Plates: {summary['total_plates_detected']}")
            print(f"  Avg Plates/Image: {summary['average_plates_per_image']:.1f}")
            
            if args.json:
                output = print_batch_results_json(results)
                print("\nDetailed Results (JSON):")
                print(output)
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"\nResults saved to {args.output}")
            elif args.csv:
                csv_output = args.output if args.output else 'results.csv'
                export_to_csv(results, csv_output)
                print(f"\nResults saved to {csv_output}")
            else:
                print("\nDetailed Results:")
                for result in results:
                    print(f"\n{result['image']}:")
                    if result['success']:
                        print_results_table(result['image'], result['plates'])
                    else:
                        print(f"  Error: {result['error']}")
                
                if args.output:
                    export_to_csv(results, args.output)
                    print(f"\nResults saved to {args.output}")
            
            # Exit with error if any processing failed
            failed_count = sum(1 for r in results if not r['success'])
            sys.exit(0 if failed_count == 0 else 1)
    
    except KeyboardInterrupt:
        print("\n\nAborted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {format_error_message(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
