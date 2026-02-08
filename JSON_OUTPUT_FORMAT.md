# JSON Output Format - Updated

The JSON output now includes both the extracted number plates AND all detected text from the image.

## New JSON Structure

```json
{
  "image": "vehicle/444R104022602182_vehicle.jpg",
  "plates": [
    {
      "text": "MH 01 AB 1234",
      "confidence": 95.5
    }
  ],
  "plate_count": 1,
  "all_detected_text": [
    {
      "text": "First detected text",
      "confidence": 92.3
    },
    {
      "text": "Second detected text",
      "confidence": 88.5
    },
    {
      "text": "MH 01 AB 1234",
      "confidence": 95.5
    }
  ],
  "total_text_blocks": 3
}
```

## Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `image` | string | Path to the processed image |
| `plates` | array | Array of detected number plates (post-processed) |
| `plate_count` | number | Total number of plates detected |
| `all_detected_text` | array | ALL text detected by AWS Textract (before filtering) |
| `total_text_blocks` | number | Total number of text blocks detected |

## Difference Between `plates` and `all_detected_text`

### `plates` (Post-Processed)
- Only contains text that matches the number plate regex pattern
- Filtered by confidence threshold
- Merged adjacent words if applicable
- This is what you want to use for actual number plate extraction

### `all_detected_text` (Raw Detection)
- Contains ALL text detected by AWS Textract
- Includes every line/block with confidence score
- Useful for debugging and understanding what the API detected
- May include noise or unrelated text from the image

## Usage Examples

### Single Image with JSON Output
```bash
python src/main.py --image vehicle/444R104022602182_vehicle.jpg --json
```

### Single Image Saved to File
```bash
python src/main.py --image vehicle/444R104022602182_vehicle.jpg --json --output results.json
```

### Batch Processing with JSON
```bash
python src/main.py --folder vehicle --json --output batch_results.json
```

## Example Response

When you run the tool with `--json`, you'll see:

```json
{
  "image": "vehicle/sample.jpg",
  "plates": [
    {
      "text": "DL 01 CD 1234",
      "confidence": 97.2
    }
  ],
  "plate_count": 1,
  "all_detected_text": [
    {
      "text": "VEHICLE",
      "confidence": 89.1
    },
    {
      "text": "REG:",
      "confidence": 91.5
    },
    {
      "text": "DL 01 CD 1234",
      "confidence": 97.2
    },
    {
      "text": "OWNER",
      "confidence": 85.3
    }
  ],
  "total_text_blocks": 4
}
```

## Console Output (Table Format)

When using the default table format, you only see the plates:

```
Image: vehicle/sample.jpg
──────────────────────────────
Plate Number │ Confidence
──────────────────────────────
DL 01 CD 1234│ 97.2%
──────────────────────────────
```

But with `--json`, you get the complete data including all detected text for analysis.

## Use Cases for `all_detected_text`

1. **Debugging**: See what Textract actually detected in the image
2. **Analysis**: Extract other information beyond plates (owner names, dates, etc.)
3. **Quality Control**: Verify that the API is working correctly
4. **Machine Learning**: Use as training data for custom models
5. **Logging**: Archive complete detection results for compliance

## File Structure (When Saved)

Files saved with `--output` will contain the full JSON response including both plates and all detected text.

```bash
python src/main.py --folder vehicle --json --output results.json
```

This saves all results including all detected text to `results.json` for later analysis.
