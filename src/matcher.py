# ocr_string_validator/src/matcher.py

def validate_text(expected, actual):
    if expected.strip().lower() == actual.strip().lower():
        return "PASS"
    else:
        return "FAIL"
