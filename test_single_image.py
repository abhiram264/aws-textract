#!/usr/bin/env python3
"""Quick test for single image"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.main import NumberPlateExtractor
from src.utils import print_results_table

# Test single image
extractor = NumberPlateExtractor(confidence=80.0)
result = extractor.process_image('vehicle/444R104022602045_vehicle.jpg', enhance=True)

print("\n" + "="*80)
print("TEST RESULT FOR: vehicle/444R104022602045_vehicle.jpg")
print("="*80)

print("\n📍 DETECTED PLATES:")
print("-" * 80)
if result['plates']:
    print_results_table(result['image'], result['plates'])
else:
    print("No plates detected\n")

print("\n📝 ALL DETECTED TEXT (RAW):")
print("-" * 80)
all_text = result.get('all_detected_text', [])
if all_text:
    for idx, text_block in enumerate(all_text, 1):
        print(f"{idx}. Text: '{text_block['text']}' | Confidence: {text_block['confidence']}%")
else:
    print("No text detected\n")
