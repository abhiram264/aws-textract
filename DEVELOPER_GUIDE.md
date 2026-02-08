# Developer Guide

## Project Architecture

This section explains how to extend and customize the Number Plate Extractor.

## Module Overview

### image_preprocessor.py

**Key Classes:**
- `ImagePreprocessor` - Static methods for image handling

**Key Methods:**
```python
ImagePreprocessor.validate_image_file(image_path)  # Returns (bool, str)
ImagePreprocessor.load_image_as_bytes(image_path)   # Returns bytes
ImagePreprocessor.load_image_with_opencv(image_path) # Returns np.ndarray
ImagePreprocessor.enhance_contrast(image_cv)        # Returns enhanced image
ImagePreprocessor.apply_bilateral_filter(image_cv)  # Returns filtered image
```

**Extending:**
- Add new image enhancement methods (e.g., `apply_histogram_equalization`)
- Add region-of-interest detection (auto-crop plate area)
- Add support for new image formats
- Add rotation/perspective correction

### textract_client.py

**Key Classes:**
- `TextractClient` - AWS Textract wrapper

**Key Methods:**
```python
client.detect_document_text(image_bytes)  # Returns Textract response
TextractClient.extract_blocks_by_type(response, 'LINE')
TextractClient.format_response(response)  # Returns structured data
```

**Extending:**
- Add async support using `boto3.Session`
- Add S3-based image handling for large batches
- Add document analysis features (forms, tables)
- Add response caching

### plate_parser.py

**Key Classes:**
- `PlateParser` - Plate extraction and parsing

**Key Methods:**
```python
parser.extract_plates(textract_blocks)  # Returns list of plates
PlateParser.filter_by_confidence(blocks, threshold)
PlateParser.merge_adjacent_words(words)
```

**Extending:**
- Add custom confidence scoring algorithms
- Add vehicle type detection
- Add plate format validation (checksums)
- Add multi-language support
- Add custom region detection

### utils.py

**Key Functions:**
```python
print_results_table(image_path, plates)
print_results_json(image_path, plates)
get_image_files(folder_path)
summarize_batch_results(results)
```

**Extending:**
- Add CSV export support
- Add database integration
- Add email/webhook notifications
- Add statistics and analytics

## Adding Custom Plate Patterns

### Option 1: Use Command-Line

```bash
python src/main.py --image car.jpg --pattern "^[A-Z]{2}-[0-9]{4}$"
```

### Option 2: Modify PlateParser

Edit `plate_parser.py`:

```python
class PlateParser:
    DEFAULT_PATTERNS = {
        'indian': r'^[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[A-Z]{2}[-\s]?[0-9]{4}$',
        'custom_format': r'^YOUR_PATTERN_HERE$',  # Add new pattern
    }
```

## Adding New Output Formats

To add CSV export, modify `utils.py`:

```python
import csv

def print_results_csv(image_path: str, plates: List[Dict]) -> str:
    """Export results as CSV"""
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Image', 'Plate', 'Confidence'])
    
    for plate in plates:
        writer.writerow([image_path, plate['text'], plate['confidence']])
    
    return output.getvalue()
```

Then update `main.py` to support `--csv` flag.

## Adding Database Support

Example: Save results to SQLite

```python
# Add to main.py
import sqlite3

def save_to_database(db_path: str, results: List[Dict]):
    """Save extraction results to SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plates (
            id INTEGER PRIMARY KEY,
            image_path TEXT,
            plate_text TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert results
    for result in results:
        for plate in result['plates']:
            cursor.execute('''
                INSERT INTO plates (image_path, plate_text, confidence)
                VALUES (?, ?, ?)
            ''', (result['image'], plate['text'], plate['confidence']))
    
    conn.commit()
    conn.close()
```

## Adding Async Support

For large batch processing, use `asyncio`:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def process_image_async(extractor, image_path):
    """Process image asynchronously"""
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=4)
    return await loop.run_in_executor(
        executor, 
        extractor.process_image, 
        image_path
    )

async def process_folder_async(extractor, folder_path):
    """Process folder with async tasks"""
    image_files = get_image_files(folder_path)
    tasks = [process_image_async(extractor, img) for img in image_files]
    return await asyncio.gather(*tasks)
```

## Adding Logging

Add to `main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

## Performance Optimization Tips

1. **Image Caching**: Cache preprocessed images
2. **Batch API Calls**: Group multiple images for API efficiency
3. **Threading**: Use ThreadPoolExecutor for folder processing
4. **Result Caching**: Cache Textract responses for identical images
5. **Lazy Loading**: Load images only when needed

## Testing the Code

Create `test_main.py`:

```python
import unittest
from src.image_preprocessor import ImagePreprocessor
from src.plate_parser import PlateParser

class TestImagePreprocessor(unittest.TestCase):
    def test_validate_image(self):
        is_valid, msg = ImagePreprocessor.validate_image_file('test.jpg')
        # Add assertions

class TestPlateParser(unittest.TestCase):
    def test_extract_plates(self):
        parser = PlateParser()
        plates = parser.extract_plates([...])
        # Add assertions

if __name__ == '__main__':
    unittest.main()
```

Run tests:
```bash
python -m unittest test_main.py
```

## Environment Variables

Add to `.env` for advanced configuration:

```
# AWS Configuration
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# Application Configuration
TEXTRACT_CONFIDENCE_THRESHOLD=80
TEXTRACT_RETRY_ATTEMPTS=3
TEXTRACT_RETRY_DELAY=1.0
IMAGE_ENHANCEMENT_ENABLED=true
DEFAULT_PLATE_PATTERN=indian

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

Update `textract_client.py`:
```python
max_retries = int(os.getenv('TEXTRACT_RETRY_ATTEMPTS', 3))
```

## Integration Examples

### Flask Web App

```python
from flask import Flask, request, jsonify
from src.main import NumberPlateExtractor

app = Flask(__name__)
extractor = NumberPlateExtractor()

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    file.save('temp.jpg')
    result = extractor.process_image('temp.jpg')
    return jsonify(result)
```

### Discord Bot

```python
import discord
from discord.ext import commands
from src.main import NumberPlateExtractor

bot = commands.Bot()
extractor = NumberPlateExtractor()

@bot.command(name='extract')
async def extract_plate(ctx):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        await attachment.save('temp.jpg')
        result = extractor.process_image('temp.jpg')
        await ctx.send(f"Detected plates: {result['plates']}")
```

## Code Style Guidelines

- Use type hints for all functions
- Add docstrings with Args, Returns, and Raises sections
- Follow PEP 8 naming conventions
- Max line length: 100 characters
- Use f-strings for formatting

## Common Issues & Solutions

### Issue: Plates not detected
- **Solution**: Lower confidence threshold, try without enhancement

### Issue: Slow processing
- **Solution**: Process images asynchronously, disable enhancement

### Issue: Memory usage
- **Solution**: Process large batches in smaller chunks, use generators

### Issue: AWS API errors
- **Solution**: Check credentials, enable Textract in region, check quotas

## Resources

- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Boto3 Textract Guide](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Pillow Documentation](https://pillow.readthedocs.io/)

## Contributing

When extending the project:

1. Write modular, testable code
2. Add comprehensive docstrings
3. Handle edge cases and errors
4. Update documentation
5. Test with sample images
6. Follow existing code style
