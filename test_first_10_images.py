#!/usr/bin/env python3
"""
Test script to process only the first N images from the vehicle folder
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.main import NumberPlateExtractor
from src.utils import get_image_files, print_results_table, print_batch_results_json


def process_first_n_images(folder_path: str, n: int = 10, json_output: bool = False, output_file: str = None):
    """
    Process only the first N images from a folder
    
    Args:
        folder_path: Path to the image folder
        n: Number of images to process
        json_output: Output as JSON
        output_file: Save results to file
    """
    print(f"Processing first {n} images from: {folder_path}\n")
    
    try:
        # Get all image files
        image_files = get_image_files(folder_path)
        
        if not image_files:
            print(f"No image files found in {folder_path}")
            return
        
        # Limit to first N
        images_to_process = image_files[:n]
        print(f"Found {len(image_files)} total images, processing {len(images_to_process)}\n")
        
        # Initialize extractor
        extractor = NumberPlateExtractor(confidence=80.0)
        
        # Process each image
        results = []
        for image_path in images_to_process:
            result = extractor.process_image(image_path, enhance=True)
            results.append(result)
        
        # Display results
        print("\n" + "="*80)
        print("PROCESSING COMPLETE")
        print("="*80)
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        total_plates = sum(len(r.get('plates', [])) for r in results if r['success'])
        
        print(f"\nSummary:")
        print(f"  Images processed: {len(results)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")
        print(f"  Total plates detected: {total_plates}")
        
        # Detailed results
        print(f"\n" + "="*80)
        print("DETAILED RESULTS")
        print("="*80)
        
        if json_output:
            for result in results:
                print(f"\n{result['image']}:")
                if result['success']:
                    import json
                    output = {
                        'plates': result['plates'],
                        'all_detected_text': result.get('all_detected_text', [])
                    }
                    print(json.dumps(output, indent=2))
                else:
                    print(f"  Error: {result['error']}")
        else:
            for result in results:
                print(f"\n{'='*80}")
                print(f"IMAGE: {result['image']}")
                print(f"{'='*80}")
                if result['success']:
                    # Show plates
                    print("\n📍 DETECTED PLATES:")
                    print("-" * 80)
                    if result['plates']:
                        print_results_table(result['image'], result['plates'])
                    else:
                        print("No plates detected\n")
                    
                    # Show all detected text (raw text)
                    all_text = result.get('all_detected_text', [])
                    print("\n📝 ALL DETECTED TEXT (RAW):")
                    print("-" * 80)
                    if all_text:
                        for idx, text_block in enumerate(all_text, 1):
                            print(f"{idx}. Text: '{text_block['text']}' | Confidence: {text_block['confidence']}%")
                    else:
                        print("No text detected\n")
                else:
                    print(f"  Error: {result['error']}")
        
        # Save to file if requested
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n✓ Results saved to: {output_file}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    # Process first 10 images
    # Change the number in process_first_n_images() to process a different count
    
    process_first_n_images(
        folder_path='vehicle',
        n=10,
        json_output=False,  # Set to True for JSON output
        output_file=None    # Set to 'results_first_10.json' to save to file
    )
