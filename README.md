# AWS Textract Number Plate Extractor

A Python CLI tool to extract number plate text from vehicle images using AWS Textract.

## Features

- Extract number plate text from local vehicle images
- AWS Textract integration with synchronous API calls
- Configurable confidence threshold filtering
- Support for custom number plate regex patterns
- Batch processing of multiple images from a folder
- JSON and table output formats

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
python src/main.py --image /path/to/image.jpg
```

### Folder of Images
```bash
python src/main.py --folder /path/to/folder
```

### Custom Options
```bash
# Set confidence threshold
python src/main.py --image image.jpg --confidence 90

# Output as JSON
python src/main.py --folder ./images --json

# Use custom plate pattern
python src/main.py --image image.jpg --pattern "^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$"
```

## Output

Results are displayed as a formatted table by default, or as JSON with the `--json` flag.

### Table Format
```
Image: car1.jpg
┌──────────────┬────────────┐
│ Plate Number │ Confidence │
├──────────────┼────────────┤
│ MH-01-AB-1234│ 95.5%      │
└──────────────┴────────────┘
```

### JSON Format
```json
{
  "image": "car1.jpg",
  "plates": [
    {
      "text": "MH-01-AB-1234",
      "confidence": 95.5
    }
  ]
}
```

## Project Structure

```
aws-textract/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── src/
    ├── __init__.py
    ├── main.py
    ├── textract_client.py
    ├── image_preprocessor.py
    ├── plate_parser.py
    └── utils.py
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
