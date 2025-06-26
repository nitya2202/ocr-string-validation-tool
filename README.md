# OCR-Based String Validation Tool (PoC)

This is a proof-of-concept implementation of a tool that automates multilingual screen content validation using Optical Character Recognition (OCR). Originally built to accelerate and improve the string verification process in medical devices, this tool is domain-agnostic and can be extended to any system that displays UI strings — including industrial systems, embedded devices, and even desktop/web applications.

---

## Why This Tool
Traditionally, validating strings on device UIs across different test protocols and languages is a manual, error-prone, and time-consuming process. In one real-world use case, this tool helped cut validation time from **16 man-months to a few days**, while eliminating the risk of human oversight.

---

## How It Works
1. **Screenshots** of device UI are provided as `.png` files.
2. A test protocol CSV lists what strings are expected on each screen per step.
3. You annotate each string's location on screen using a built-in annotation tool.
4. The tool:
   - Crops regions from screenshots based on your annotations
   - Uses Tesseract OCR to extract text
   - Compares OCR output to expected strings
   - Logs results (`PASS` or `FAIL`) into a CSV report

---

## Folder Structure
```
ocr_string_validator/
├── src/                         # Source code
│   ├── main.py                  # Main script to run validation
│   ├── annotate_coordinates.py # Interactive tool to mark string locations
│   ├── ocr_utils.py            # OCR logic
│   └── matcher.py              # String comparison logic
├── data/
│   ├── screenshots/            # Input images (screens)
│   ├── expected_strings/en-US.json # StringID to actual text mapping
│   ├── test_protocol.csv       # StepID + ScreenID + ExpectedStringID
│   └── string_coordinates.csv  # Bounding boxes for each Step/Screen/String
├── output/
│   └── results-en-US.csv       # Validation results
```

---

## Setup
1. Install dependencies:
```bash
pip install pytesseract pillow opencv-python
```
2. Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and make sure it's added to your system `PATH`.

---

## Run the Tool
### Step 1: Annotate string regions
```bash
python src/annotate_coordinates.py
```
Use the GUI to draw boxes and input the `ExpectedStringID` for each region.

### Step 2: Run OCR validation
```bash
python src/main.py
```
Check the results in `output/results-en-US.csv`

---

## Design Notes
- The `ExpectedStringID` is the central link between the protocol, string mapping, and coordinates.
- Only the `en-US.json` contains actual string values — this ensures consistency and reusability.
- Fully scalable: you can add more steps, screens, languages, and reuse annotations.

---

## Future Enhancements
- Fuzzy matching (e.g., Levenshtein distance)
- Multilingual support via Tesseract `lang` switch
- CLI flags for language selection and batch runs
- GUI preview of annotated regions for review

---

## Author Note
This PoC demonstrates the power of targeted automation in regulated, high-accuracy environments. Originally built in a medical device context, it’s designed to be flexible, fast, and robust for real-world scale.

---

Feel free to fork, adapt, or contribute!