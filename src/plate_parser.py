"""Plate number parser module for extracting number plates from Textract results"""

import re
from typing import List, Dict, Tuple, Optional


# Known Indian state/UT codes (2-letter)
INDIAN_STATE_CODES = {
    'AN', 'AP', 'AR', 'AS', 'BR', 'CG', 'CH', 'DD', 'DL', 'GA', 'GJ', 'HP',
    'HR', 'JH', 'JK', 'KA', 'KL', 'LA', 'LD', 'MH', 'ML', 'MN', 'MP', 'MZ',
    'NL', 'OD', 'PB', 'PY', 'RJ', 'SK', 'TG', 'TN', 'TR', 'TS', 'UK', 'UP',
    'WB',
}

# Common OCR confusables: what gets misread as what
# Used only in digit positions
OCR_DIGIT_FIXES = {'O': '0', 'I': '1', 'l': '1', 'S': '5', 'B': '8', 'G': '6', 'D': '0'}
OCR_LETTER_FIXES = {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '6': 'G'}

# Junk / noise words to ignore completely
NOISE_WORDS = {
    'IND', 'NO', 'ND', 'MC', 'HIRE', 'FOR', 'GOODS', 'CARRIER', 'CONTRACT',
    'CARRIAGE', 'GOVT', 'HICLE', 'VEHICLE', 'AUTO', 'MOTOR', 'CAB', 'CNG',
    'ASHOK', 'LEYLAND', 'ASHOKILEYLAND', 'TATA', 'SIGNA', 'EICHER', 'KIA',
    'ISUZU', 'BHARATBENZ', 'MAHINDRA', 'POLICE', 'LAKSHMI', 'KRISHNA',
    'PVT', 'LTD', 'SUPER', 'ROCKET', 'RANGE', 'ROVER', 'DRIVING',
    'ROAD', 'KING', 'SECTION', 'AMOUNT', 'FRESH', 'FRESS',
    'SPEED', 'CLASS', 'PLATE', 'LANE', 'DATE', 'RHS', 'LHS', 'CH',
    'CAR', 'BIKE', 'TRUCK', 'LCV', 'BUS',
    'THE', 'AND', 'OF', 'IN', 'ON', 'AT', 'TO', 'IS', 'IT', 'IF',
    'PP', 'CK', 'KO', 'AO', 'LI', 'RE', 'DE', 'BE', 'YK', 'YS',
    'ARM', 'CII', 'NZB', 'ISI', 'PO', 'JAI', 'SANTOS', 'HILL',
    'PRO', 'EUTECH', 'EUTECH6', 'MEONAME',
}

# Prefixes to strip before parsing
STRIP_PREFIXES = ['(ND)', 'IND', 'NO', 'ND']


class PlateParser:
    """Parse and extract number plates from Textract responses"""

    # Multiple Indian plate patterns (flexible)
    INDIAN_PATTERNS = [
        # Standard: XX 00 XX 0000  (e.g. TS 08 FW 3131, AP 29 BP 2496)
        r'^([A-Z]{2})[-.\s]?(\d{2})[-.\s]?([A-Z]{1,3})[-.\s]?(\d{3,4})$',
        # With single letter series: XX 00 X 0000  (e.g. TG 08 D 8599, TS 36 T 1330)
        r'^([A-Z]{2})[-.\s]?(\d{2})[-.\s]?([A-Z])[-.\s]?(\d{4})$',
        # Compact: XX00XX0000  (e.g. TS08FW3131, AP05CH2525)
        r'^([A-Z]{2})(\d{2})([A-Z]{1,3})(\d{3,4})$',
        # With spaces in number: XX 00 XX 0000 (already covered but explicit)
        r'^([A-Z]{2})\s(\d{2})\s([A-Z]{1,2})\s(\d{4,5})$',
        # Format like NL01A J0044 (letter attached to district, then space + alphanumeric)
        r'^([A-Z]{2})[-.\s]?(\d{2})([A-Z])[-.\s]([A-Z]\d{4})$',
        # Format like HR73B 9259 (letter attached to district, then space + digits)
        r'^([A-Z]{2})[-.\s]?(\d{2})([A-Z])[-.\s](\d{4,5})$',
        # Format like GJ18B V5038 (letter attached to district, then space + alphanumeric)
        r'^([A-Z]{2})[-.\s]?(\d{2})([A-Z])[-.\s]([A-Z]\d{3,4})$',
        # TG 10 A 9999 with extra spaces
        r'^([A-Z]{2})\s+(\d{2})\s+([A-Z]{1,2})\s+(\d{3,4})$',
        # Format: XX00 XX 0000 (e.g. TS08 JX4468 or TS08 JR2726)
        r'^([A-Z]{2})(\d{2})\s([A-Z]{1,3})[-.\s]?(\d{3,4})$',
        # Format like TG16Z 0106 (series letter attached to district)
        r'^([A-Z]{2})(\d{2})([A-Z])[-.\s](\d{4})$',
        # Format: XX 00XX0000 (e.g. TS 08UJ0793)
        r'^([A-Z]{2})\s(\d{2})([A-Z]{1,3})(\d{3,4})$',
        # Alternate: AP 16 F J6249
        r'^([A-Z]{2})\s(\d{2})\s([A-Z])\s([A-Z]\d{4})$',
        # Format: TS10F A4680
        r'^([A-Z]{2})(\d{2})([A-Z])\s([A-Z]\d{4})$',
        # Format: TS08FM 1206 (series attached, number separate)
        r'^([A-Z]{2})(\d{2})([A-Z]{2})\s(\d{3,4})$',
        # Format: AP 10BA4575 (space after state)
        r'^([A-Z]{2})\s(\d{2})([A-Z]{2})(\d{4})$',
    ]

    def __init__(self, confidence_threshold: float = 60.0, pattern: str = None):
        """
        Initialize plate parser

        Args:
            confidence_threshold: Minimum confidence percentage (0-100)
            pattern: Custom regex pattern for plate matching (defaults to Indian patterns)
        """
        self.confidence_threshold = confidence_threshold

        if pattern:
            self.custom_pattern = re.compile(pattern, re.IGNORECASE)
        else:
            self.custom_pattern = None

        self.compiled_patterns = [re.compile(p) for p in self.INDIAN_PATTERNS]

    # ------------------------------------------------------------------ #
    #                        TEXT CLEANING                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def clean_raw_text(text: str) -> str:
        """
        Aggressively clean raw OCR text before attempting plate matching.

        Handles:
        - Leading/trailing quotes, hyphens, dots, parentheses, commas
        - IND / NO / (ND) prefixes
        - Dots used as separators (TN.52 → TN52)
        - Embedded hyphens in plate body (U-D → UD)
        - Speed-camera overlay "Plate: XXXXX" extraction
        """
        if not text:
            return ''

        t = text.strip()

        # ---- Extract from speed-camera overlay "Plate: XXXXX" ----
        plate_match = re.search(r'Plate:\s*([A-Z0-9\s]{6,15})', t, re.IGNORECASE)
        if plate_match:
            t = plate_match.group(1).strip()

        # ---- Strip known prefixes ----
        for prefix in STRIP_PREFIXES:
            if t.upper().startswith(prefix + ' ') or t.upper().startswith(prefix + '\t'):
                t = t[len(prefix):].strip()
            # Also handle no-space variant like "INDTS..."
            elif t.upper().startswith(prefix) and len(t) > len(prefix) and t[len(prefix)].isalpha():
                t = t[len(prefix):].strip()

        # ---- Strip leading / trailing junk characters ----
        t = t.strip('"\'()[]{}.,;:!?*# ')
        # Strip leading/trailing hyphens but keep internal ones for now
        t = t.strip('-')

        # ---- Remove dots used as separators (TN.52 L.0083 → TN52 L0083) ----
        t = re.sub(r'\.', '', t)

        # ---- Remove embedded hyphens between letters/digits (U-D → UD) ----
        t = re.sub(r'(?<=[A-Za-z0-9])-(?=[A-Za-z0-9])', '', t)

        # ---- Collapse multiple spaces ----
        t = re.sub(r'\s+', ' ', t).strip()

        return t

    @staticmethod
    def fix_ocr_confusables(text: str) -> str:
        """
        Fix common OCR misreads based on expected plate structure.
        Indian plates: SS DD LL NNNN  (State-2, District-2digits, Series-letters, Number-digits)
        We try to fix characters that are in the wrong class.
        """
        clean = text.replace(' ', '').replace('-', '')
        if len(clean) < 7 or len(clean) > 13:
            return text  # too short / long, don't guess

        # Try to identify state code (first 2 should be letters)
        result = list(text)
        # Fix first two chars to letters
        idx = 0
        char_idx = 0
        while idx < len(result) and char_idx < 2:
            if result[idx] in (' ', '-'):
                idx += 1
                continue
            if result[idx] in OCR_LETTER_FIXES:
                result[idx] = OCR_LETTER_FIXES[result[idx]]
            idx += 1
            char_idx += 1

        # Fix next two chars to digits (district code)
        char_idx = 0
        while idx < len(result) and char_idx < 2:
            if result[idx] in (' ', '-'):
                idx += 1
                continue
            if result[idx] in OCR_DIGIT_FIXES:
                result[idx] = OCR_DIGIT_FIXES[result[idx]]
            idx += 1
            char_idx += 1

        return ''.join(result)

    @staticmethod
    def is_noise(text: str) -> bool:
        """Check if a text block is noise / not plate-related"""
        t = text.strip().upper().rstrip('.-:,;!?')
        # Single char
        if len(t) <= 1:
            return True
        # Pure noise word
        if t in NOISE_WORDS:
            return True
        # Looks like a timestamp  HH:MM:SS or date
        if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', t):
            return True
        if re.match(r'^\d{4}-\d{2}-\d{2}', t):
            return True
        # Speed overlay fragments  "XX km/h", "420 RHS", etc.
        if re.match(r'^\d+\s*km/h$', t, re.IGNORECASE):
            return True
        if re.match(r'^[\d+]*\s*RHS$', t, re.IGNORECASE):
            return True
        if re.match(r'^[\d+]*\s*LHS$', t, re.IGNORECASE):
            return True
        # Gmail / urls
        if '@' in t or 'gmail' in t.lower():
            return True
        return False

    # ------------------------------------------------------------------ #
    #                     PLATE MATCHING                                   #
    # ------------------------------------------------------------------ #

    def matches_plate_pattern(self, text: str) -> bool:
        """Check if text matches any known Indian plate pattern"""
        if self.custom_pattern:
            return bool(self.custom_pattern.match(text))

        t = text.upper().strip()
        for pat in self.compiled_patterns:
            if pat.match(t):
                return True
        return False

    def validate_state_code(self, text: str) -> bool:
        """Check if the first 2 letters are a valid Indian state code"""
        clean = text.replace(' ', '').replace('-', '').upper()
        if len(clean) >= 2:
            return clean[:2] in INDIAN_STATE_CODES
        return False

    @staticmethod
    def filter_by_confidence(blocks: List[Dict], threshold: float) -> List[Dict]:
        """Filter blocks by confidence threshold"""
        return [block for block in blocks if block.get('confidence', 0) >= threshold]

    @staticmethod
    def merge_adjacent_words(words: List[Dict]) -> List[str]:
        """
        Merge adjacent words to form potential license plate strings
        """
        if not words:
            return []

        merged = []
        current_text = words[0].get('text', '')
        current_group = [words[0]]

        for i in range(1, len(words)):
            word = words[i]
            prev_word = current_group[-1]

            prev_geometry = prev_word.get('geometry', {})
            curr_geometry = word.get('geometry', {})

            prev_right = prev_geometry.get('BoundingBox', {}).get('Left', 0) + \
                         prev_geometry.get('BoundingBox', {}).get('Width', 0)
            curr_left = curr_geometry.get('BoundingBox', {}).get('Left', 0)

            if curr_left - prev_right < 0.05:  # Widened threshold for close words
                current_text += ' ' + word.get('text', '')
                current_group.append(word)
            else:
                if current_text.strip():
                    merged.append(current_text.strip())
                current_text = word.get('text', '')
                current_group = [word]

        if current_text.strip():
            merged.append(current_text.strip())

        return merged

    def _try_match(self, text: str, confidence: float) -> Optional[Dict]:
        """
        Try to match a text string as a plate. Applies cleaning, OCR fixes, etc.
        Returns a plate dict or None.
        """
        # Step 1: clean
        cleaned = self.clean_raw_text(text)
        if not cleaned or len(cleaned) < 5:
            return None

        # Step 2: skip noise
        if self.is_noise(cleaned):
            return None

        # Step 3: try direct match
        if self.matches_plate_pattern(cleaned) and self.validate_state_code(cleaned):
            return {'text': cleaned, 'confidence': confidence}

        # Step 4: try OCR fix
        fixed = self.fix_ocr_confusables(cleaned)
        if fixed != cleaned and self.matches_plate_pattern(fixed) and self.validate_state_code(fixed):
            return {'text': fixed, 'confidence': confidence}

        return None

    def extract_plates(self, textract_blocks: List[Dict]) -> List[Dict]:
        """
        Extract number plates from Textract blocks.
        Uses a multi-pass approach:
          1. Try each block individually (high + low confidence)
          2. Try merging 2-3 adjacent blocks
          3. Try extracting from speed-camera overlay text ("Plate: XXX")
        """
        if not textract_blocks:
            return []

        plates = []
        plate_texts_found = set()

        def _add(plate_dict, block_type='single'):
            norm = plate_dict['text'].replace(' ', '').upper()
            if norm not in plate_texts_found:
                plate_texts_found.add(norm)
                plates.append({
                    'text': plate_dict['text'],
                    'confidence': plate_dict['confidence'],
                    'block_type': block_type
                })

        # ---------- Pass 1: individual blocks (all confidences) ----------
        for block in textract_blocks:
            text = block.get('text', '').strip()
            conf = block.get('confidence', 0)
            if not text or conf < self.confidence_threshold:
                continue

            result = self._try_match(text, conf)
            if result:
                _add(result, 'single')

        # ---------- Pass 2: combine 2-3 consecutive non-noise blocks ------
        # Filter to blocks above threshold that aren't pure noise
        usable = []
        for block in textract_blocks:
            text = block.get('text', '').strip()
            conf = block.get('confidence', 0)
            if not text or conf < self.confidence_threshold:
                continue
            cleaned = self.clean_raw_text(text)
            if cleaned and not self.is_noise(cleaned):
                usable.append({'text': cleaned, 'confidence': conf, 'geometry': block.get('geometry', {})})

        for i in range(len(usable)):
            for j in range(i + 1, min(i + 4, len(usable))):
                parts = [usable[k]['text'] for k in range(i, j + 1)]
                combined = ' '.join(parts)
                avg_conf = sum(usable[k]['confidence'] for k in range(i, j + 1)) / (j - i + 1)
                result = self._try_match(combined, avg_conf)
                if result:
                    _add(result, 'merged')

        # ---------- Pass 3: extract "Plate: XXX" from overlay text --------
        for block in textract_blocks:
            text = block.get('text', '').strip()
            conf = block.get('confidence', 0)
            plate_match = re.search(r'Plate:\s*([A-Z0-9]{6,15})', text, re.IGNORECASE)
            if plate_match:
                candidate = plate_match.group(1).strip()
                result = self._try_match(candidate, conf)
                if result:
                    _add(result, 'overlay')

        # ---------- Pass 4: merge adjacent words by geometry ---------------
        above_threshold = self.filter_by_confidence(textract_blocks, self.confidence_threshold)
        merged_texts = self.merge_adjacent_words(above_threshold)
        for merged_text in merged_texts:
            avg_conf = sum(b.get('confidence', 0) for b in above_threshold) / len(above_threshold) \
                if above_threshold else 0
            result = self._try_match(merged_text, avg_conf)
            if result:
                _add(result, 'adjacent')

        # Sort by confidence descending
        plates.sort(key=lambda x: x['confidence'], reverse=True)
        return plates

    @staticmethod
    def format_plates(plates: List[Dict]) -> List[Dict]:
        """Format extracted plates for output"""
        return [
            {
                'text': plate['text'],
                'confidence': round(plate['confidence'], 2)
            }
            for plate in plates
        ]

    @staticmethod
    def clean_plate_text(text: str) -> str:
        """Clean plate text by removing extra spaces and normalizing format"""
        text = re.sub(r'\s+', ' ', text).strip()
        text = text.replace('- ', '-').replace(' -', '-')
        return text

    @staticmethod
    def validate_plate(text: str) -> bool:
        """Basic validation for plate text"""
        clean_text = text.replace(' ', '').replace('-', '')
        if not clean_text.isalnum():
            return False
        if len(clean_text) < 7 or len(clean_text) > 13:
            return False
        return True


def get_all_detected_text(textract_response: Dict) -> List[Dict]:
    """
    Extract all detected text from Textract response
    """
    lines = textract_response.get('lines', [])
    return [
        {
            'text': line.get('text', ''),
            'confidence': round(line.get('confidence', 0), 2)
        }
        for line in lines
        if line.get('text', '').strip()
    ]


def parse_plates_from_textract(
    textract_response: Dict,
    confidence_threshold: float = 60.0,
    pattern: str = None,
    include_low_confidence: bool = False,
    low_confidence_threshold: float = 30.0
) -> Dict:
    """
    Parse number plates and all text from a Textract response

    Args:
        textract_response: Formatted Textract response
        confidence_threshold: Minimum confidence percentage for plates
        pattern: Custom regex pattern for plate matching
        include_low_confidence: Include plates below confidence_threshold
        low_confidence_threshold: Minimum confidence for low confidence plates
    """
    parser = PlateParser(
        confidence_threshold=confidence_threshold,
        pattern=pattern
    )

    lines = textract_response.get('lines', [])

    # Extract plates from lines
    plates = parser.extract_plates(lines)
    formatted_plates = parser.format_plates(plates)

    # Extract low confidence plates if requested
    low_confidence_plates = []
    if include_low_confidence:
        low_parser = PlateParser(
            confidence_threshold=low_confidence_threshold,
            pattern=pattern
        )
        low_plates = low_parser.extract_plates(lines)

        for plate in low_plates:
            if plate['confidence'] < confidence_threshold and plate['confidence'] >= low_confidence_threshold:
                plate_text = plate['text']
                if not any(p['text'] == plate_text for p in formatted_plates):
                    low_confidence_plates.append({
                        'text': plate['text'],
                        'confidence': round(plate['confidence'], 2),
                        'is_low_confidence': True
                    })

        formatted_plates.extend(low_confidence_plates)

    all_text = get_all_detected_text(textract_response)

    return {
        'plates': formatted_plates,
        'all_detected_text': all_text,
        'low_confidence_plates_included': include_low_confidence
    }
