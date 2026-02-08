# AWS Textract Number Plate Extractor

A Python CLI tool to extract Indian vehicle number plates from images using AWS Textract.

## Features

- Extract number plates from vehicle and number plate images using AWS Textract
- **Smart plate parsing** with 15+ Indian plate format patterns
- **OCR noise filtering** — strips junk prefixes (`IND`, `NO`, `(ND)`), brand names, speed-camera overlay text
- **OCR confusable correction** — fixes common misreads like `O`→`0`, `B`→`8` in digit positions
- **Speed-camera overlay extraction** — pulls plate numbers from `Plate: XXXXX` overlays
- **Indian state code validation** — only accepts plates starting with valid state/UT codes
- Configurable confidence threshold (default: 60%)
- Support for custom number plate regex patterns
- Batch processing of multiple images from a folder
- CSV, JSON, and table output formats
- Image preprocessing and enhancement
- Low-confidence plate inclusion with `--include-low-confidence`

## Prerequisites

- Python 3.9 or higher
- AWS Account with Textract API access
- AWS credentials (Access Key ID and Secret Access Key)

## Installation

1. Clone or download the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up AWS credentials:
   ```bash
   cp .env.example .env
   # Edit .env and add your AWS credentials
   ```

## Usage

### Single Image
```bash
python src/main.py --image vehicle/car.jpg
```

### Folder of Images
```bash
python src/main.py --folder vehicle
```

### CSV Output
```bash
# Process number plate images and export to CSV
python src/main.py --folder number_plate --csv --output plates.csv

# Process vehicle images and export to CSV
python src/main.py --folder vehicle --csv --output vehicle_plates.csv
```

### Custom Options
```bash
# Set confidence threshold (default: 60)
python src/main.py --folder vehicle --confidence 30

# Include low-confidence plates (30-60%) separately tagged
python src/main.py --folder vehicle --csv --output results.csv --include-low-confidence --low-confidence-threshold 30

# Output as JSON
python src/main.py --folder vehicle --json

# Save JSON to file
python src/main.py --folder vehicle --json --output results.json

# Disable image enhancement
python src/main.py --image car.jpg --no-enhance

# Use custom plate regex pattern
python src/main.py --image car.jpg --pattern "^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"

# Specify AWS region
python src/main.py --image car.jpg --region ap-south-1
```

## Output Formats

### CSV Format (Recommended for batch)
```
Image Name,Raw Output (All Detected Words),Number Plates,Confidence Score
vehicle\car1.jpg,TATA | TS08FW3131,TS08FW3131,95.17%
vehicle\car2.jpg,ASHOK LEYLAND | TS 16 | Z0258,TS 16 Z0258,99.41%
```

### Table Format
```
Image: car1.jpg
--------------------------------------------------
+----------------+------------+
| Plate Number   | Confidence |
+----------------+------------+
| TS08FW3131     | 95.2%      |
+----------------+------------+
```

### JSON Format
```json
{
  "image": "car1.jpg",
  "plates": [
    {
      "text": "TS08FW3131",
      "confidence": 95.17
    }
  ],
  "plate_count": 1,
  "all_detected_text": [
    { "text": "TATA", "confidence": 92.5 },
    { "text": "TS08FW3131", "confidence": 95.17 }
  ]
}
```

## Plate Parsing Details

The parser handles a wide variety of Indian number plate formats and OCR artifacts:

### Supported Plate Formats
| Format | Example |
|--------|---------|
| Compact | `TS08FW3131`, `AP05CH2525` |
| Spaced | `TS 08 FW 3131`, `AP 29 BP 2496` |
| Single series | `TG 08 D 8599`, `TS 36 T 1330` |
| Mixed spacing | `TS08 JX4468`, `NL01A J0044` |
| Series attached | `TG16Z 0106`, `HR73B 9259` |

### Automatic Cleaning
- Strips `IND`, `NO`, `(ND)` prefixes from plate text
- Removes dots used as separators (`TN.52 L.0083` → `TN52 L0083`)
- Removes embedded hyphens (`TS12 U-D 3364` → `TS12 UD 3364`)
- Strips leading/trailing quotes, hyphens, and special characters
- Filters out brand names, timestamps, speed overlays, and other noise
- Extracts plates from speed-camera overlay text (`Plate: TS13EB4370`)
- Fixes OCR misreads (`O`↔`0`, `B`↔`8`) based on expected character position

### Validated State Codes
All 37 Indian state and union territory codes are recognized:
`AN, AP, AR, AS, BR, CG, CH, DD, DL, GA, GJ, HP, HR, JH, JK, KA, KL, LA, LD, MH, ML, MN, MP, MZ, NL, OD, PB, PY, RJ, SK, TG, TN, TR, TS, UK, UP, WB`

## Project Structure

```
aws-textract/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── src/
    ├── __init__.py
    ├── main.py              # CLI entry point
    ├── textract_client.py    # AWS Textract API wrapper
    ├── image_preprocessor.py # Image enhancement before OCR
    ├── plate_parser.py       # Number plate extraction & cleaning
    └── utils.py              # CSV/JSON export & display utilities
```

## Configuration

Edit the `.env` file with your AWS credentials:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

## License

MIT
