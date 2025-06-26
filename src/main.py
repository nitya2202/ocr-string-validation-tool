# ocr_string_validator/src/main.py

import os
import csv
from pathlib import Path
from ocr_utils import extract_text_from_image_region
from matcher import validate_text
import json

# Configs
DATA_DIR = Path("./data")
PROTOCOL_FILE = DATA_DIR / "test_protocol.csv"
STRING_MAP_FILE = DATA_DIR / "expected_strings" / "en-US.json"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
COORDINATE_FILE = DATA_DIR / "string_coordinates.csv"
OUTPUT_FILE = Path("./output") / "results-en-US.csv"

os.makedirs(OUTPUT_FILE.parent, exist_ok=True)

# Load expected strings
with open(STRING_MAP_FILE, 'r', encoding='utf-8') as f:
    expected_strings = json.load(f)

# Load test protocol
with open(PROTOCOL_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    protocol = list(reader)

# Load string coordinates with StepID included
coordinates = {}
with open(COORDINATE_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = (row['StepID'], row['ScreenID'], row['ExpectedStringID'])
        coordinates[key] = (int(row['Left']), int(row['Top']), int(row['Right']), int(row['Bottom']))

# Run OCR and validation
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Step ID", "Screen ID", "Expected String", "OCR Output", "Match Result"])

    for step in protocol:
        step_id = step['StepID']
        screen_id = step['ScreenID']
        string_key = step['ExpectedStringID']

        expected_text = expected_strings.get(string_key, "")
        image_path = SCREENSHOT_DIR / f"{screen_id}.png"

        if not image_path.exists():
            writer.writerow([step_id, screen_id, expected_text, "<Missing Image>", "FAIL"])
            continue

        coord_key = (step_id, screen_id, string_key)
        if coord_key not in coordinates:
            writer.writerow([step_id, screen_id, expected_text, "<Missing Coordinates>", "FAIL"])
            continue

        region = coordinates[coord_key]
        ocr_output = extract_text_from_image_region(str(image_path), region)
        match_result = validate_text(expected_text, ocr_output)

        writer.writerow([step_id, screen_id, expected_text, ocr_output, match_result])