# CSV Export Feature Guide

## Overview

The number plate extractor now supports CSV export with the following columns:
- **Image Name** - The path/name of the image processed
- **Raw Output (All Detected Words)** - All text detected by AWS Textract
- **Number Plates** - Extracted number plates (filtered and post-processed)
- **Confidence Score** - Confidence percentage for each plate

## Usage

### Single Image to CSV

```bash
# Export as CSV (default name: results.csv)
python src/main.py --image vehicle/sample.jpg --csv

# Export to custom filename
python src/main.py --image vehicle/sample.jpg --csv --output my_results.csv
```

### Batch Processing to CSV

```bash
# Process all images in folder and export as CSV
python src/main.py --folder vehicle --csv

# Export to custom filename
python src/main.py --folder vehicle --csv --output batch_results.csv
```

### Include Low Confidence Plates (30-80%)

```bash
# Include plates with confidence between 30% and 80%
python src/main.py --image vehicle/sample.jpg --csv --include-low-confidence

# Custom low confidence threshold (default: 30%)
python src/main.py --folder vehicle --csv --include-low-confidence --low-confidence-threshold 50
```

### Combined with Other Options

```bash
# CSV export with custom confidence threshold and low confidence plates
python src/main.py --folder vehicle --csv --output results.csv \
  --confidence 75 --include-low-confidence --low-confidence-threshold 40

# CSV export without image enhancement
python src/main.py --folder vehicle --csv --no-enhance
```

## CSV Output Format

### Example CSV Content

```
Image Name,Raw Output (All Detected Words),Number Plates,Confidence Score
vehicle/car1.jpg,"ASHOK LEYLAN (93.83%) | TS12 UD 3371 (99.88%) | 1312UD337 (21.71%)",TS12 UD 3371,99.9%
vehicle/car2.jpg,"TATA (96.58%) | NL01A (95.1%) | J0044 (99.56%)",NL01A J0044,97.3%
vehicle/car3.jpg,"TATA (96.58%) | NL01A (95.1%) | J0044 (99.56%)",NL01A J0044 (low confidence),75.5%
vehicle/car4.jpg,"Text not detected",None detected,N/A
```

### Column Descriptions

| Column | Description | Example |
|--------|-------------|---------|
| Image Name | Path to processed image | `vehicle/car1.jpg` |
| Raw Output | All detected text blocks with confidence | `ASHOK LEYLAN (93.83%) \| TS12 UD 3371 (99.88%)` |
| Number Plates | Detected number plate(s) | `TS12 UD 3371` or `NL01A J0044` |
| Confidence Score | Plate confidence percentage | `99.9%` |

## Features

✅ **Single and Multi-line Plate Detection**
- Detects plates like "NL01A J0044" (split across 2 lines)

✅ **Low Confidence Plate Support**
- Includes plates with confidence 30-80% with `--include-low-confidence`
- Custom threshold with `--low-confidence-threshold`

✅ **Complete Text Capture**
- Raw output shows ALL text detected by Textract (before filtering)
- Useful for debugging and analysis

✅ **Batch Processing**
- Process 10, 100, or 1000+ images to a single CSV file

✅ **Error Handling**
- Failed images show error messages in CSV
- Successful processing marked in Confidence Score

## Recommended Workflows

### Workflow 1: High Confidence Extraction
```bash
python src/main.py --folder vehicle --csv --output verified_plates.csv
```
Gets only plates with 80%+ confidence.

### Workflow 2: Comprehensive Capture (with Low Confidence)
```bash
python src/main.py --folder vehicle --csv --output all_plates.csv \
  --include-low-confidence --low-confidence-threshold 30
```
Gets all detected plates (high and low confidence).

### Workflow 3: Confidence Tuning
```bash
# Try different confidence thresholds
python src/main.py --folder vehicle --csv --output plates_90.csv --confidence 90
python src/main.py --folder vehicle --csv --output plates_70.csv --confidence 70
python src/main.py --folder vehicle --csv --output plates_50.csv --confidence 50
```
Export multiple CSV files at different thresholds for comparison.

## Python Usage

You can also import and use the functions programmatically:

```python
from src.utils import export_to_csv, export_to_csv_single

# Single image export
export_to_csv_single(
    image_path='vehicle/sample.jpg',
    all_text=[
        {'text': 'TATA', 'confidence': 96.58},
        {'text': 'NL01A', 'confidence': 95.1},
        {'text': 'J0044', 'confidence': 99.56}
    ],
    plates=[
        {'text': 'NL01A J0044', 'confidence': 97.3}
    ],
    output_file='results.csv'
)

# Batch export
results = [...]  # List of result dictionaries
export_to_csv(results, 'batch_results.csv')
```

## Integration with Excel/Google Sheets

The CSV files are fully compatible with:
- **Microsoft Excel** - Open directly in Excel
- **Google Sheets** - Import via File → Import → Upload
- **LibreOffice Calc** - Open directly
- **Python Pandas** - `pd.read_csv('results.csv')`
- **R** - `read.csv('results.csv')`

Example in Pandas:
```python
import pandas as pd

df = pd.read_csv('results.csv')
print(df[df['Confidence Score'].str.contains('99')])  # Get 99%+ plates
```

## Troubleshooting

### CSV file is empty
- Check that images were processed successfully
- Verify image paths are correct
- Check error messages in terminal output

### Special characters in plate numbers
- CSV properly escapes special characters
- Use UTF-8 encoding to view correctly

### Large batch files
- CSV handles files with thousands of rows
- Open in Excel or Google Sheets for better performance

## Notes

- Confidence scores are sorted highest to lowest
- Low confidence plates marked with note in output (when using `--include-low-confidence`)
- Multi-line plates combined with space separator (e.g., "NL01A J0044")
- All text in raw output format: "TEXT (Confidence%)"
