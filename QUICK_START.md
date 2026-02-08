# Quick Start Guide

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials
Copy the environment template and add your AWS credentials:
```bash
cp env.example .env
```

Edit `.env` with your AWS credentials:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

**Important:** Make sure Textract is enabled in your AWS region.

## Usage Examples

### Extract from a Single Image
```bash
python src/main.py --image path/to/car.jpg
```

### Batch Process a Folder
```bash
python src/main.py --folder path/to/images/
```

### Set Custom Confidence Threshold
```bash
# Only detect plates with 90%+ confidence
python src/main.py --image car.jpg --confidence 90
```

### Output as JSON
```bash
python src/main.py --folder ./images --json
```

### Save Results to File
```bash
python src/main.py --image car.jpg --output results.json --json
```

### Use Custom Plate Pattern
```bash
# For US license plates
python src/main.py --image car.jpg --pattern "^[A-Z]{1,3}-[0-9]{3,4}$"
```

### Disable Image Enhancement
```bash
python src/main.py --image car.jpg --no-enhance
```

## Available Plate Patterns

The tool includes built-in patterns for:
- **Indian** (default): `XX 01 AB 1234`
- **US**: `ABC-1234`
- **UK**: `AB12 ABC`
- **International**: Generic alphanumeric

You can use a custom pattern with the `--pattern` flag for any format.

## Project Architecture

```
Image → Preprocessing → Textract API → Response Parsing → Plate Extraction
```

### Components:

1. **image_preprocessor.py**
   - Image validation and loading
   - Optional image enhancement (contrast, noise reduction)
   - Format conversion for Textract

2. **textract_client.py**
   - AWS Textract API wrapper
   - Synchronous document text detection
   - Automatic retries with exponential backoff
   - Error handling

3. **plate_parser.py**
   - Textract response parsing
   - Confidence filtering
   - Regex-based plate detection
   - Text merging and validation

4. **utils.py**
   - Result formatting (table and JSON)
   - Batch processing utilities
   - Validation functions

5. **main.py**
   - CLI interface with argparse
   - Single image and batch processing modes
   - Result export to file

## Troubleshooting

### Error: "Failed to initialize Textract client"
- Check AWS credentials in `.env`
- Ensure AWS_REGION is set to a region where Textract is available
- Verify IAM permissions for Textract

### Error: "File not found" or "Unsupported format"
- Ensure image path is correct
- Check that image format is supported (JPEG, PNG, BMP, GIF, WebP)

### No plates detected
- Try lowering the `--confidence` threshold
- Use `--no-enhance` to skip preprocessing
- Try a custom pattern with `--pattern`
- Check that the plate format matches the pattern

### API Throttling
- The tool automatically retries with exponential backoff
- Consider processing images in smaller batches

## Performance Tips

1. **Batch Processing**: Process multiple images at once for better throughput
2. **Image Quality**: Ensure good lighting and clear plate visibility
3. **Preprocessing**: Default enhancement helps, but you can disable with `--no-enhance`
4. **Confidence Threshold**: Lower threshold catches more plates but may increase false positives

## Next Steps

1. Test with sample vehicle images in the `vehicle/` folder
2. Customize the plate pattern if you're not using Indian format
3. Integrate the extractor into your application using the provided modules
