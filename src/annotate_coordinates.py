# ocr_string_validator/src/annotate_coordinates.py

import cv2
import os
import csv
from pathlib import Path

def run_annotation():
    # Directory with screenshots
    SCREENSHOT_DIR = Path("./data/screenshots")
    OUTPUT_FILE = Path("./data/string_coordinates.csv")

    # Load all image files
    image_files = sorted([f for f in SCREENSHOT_DIR.glob("*.png")])

    # Open CSV writer
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["StepID", "ScreenID", "ExpectedStringID", "Left", "Top", "Right", "Bottom"])

        for img_path in image_files:
            img = cv2.imread(str(img_path))
            screen_id = img_path.stem

            print(f"\nNow annotating: {screen_id}")
            step_id = input("Enter StepID for this image: ").strip()

            while True:
                roi = cv2.selectROI(f"Mark string on {screen_id} (press ENTER to confirm, ESC to skip)", img, fromCenter=False, showCrosshair=True)
                cv2.destroyAllWindows()

                if sum(roi) == 0:
                    print("No region selected. Skipping...")
                    break

                x, y, w, h = roi
                left, top, right, bottom = x, y, x + w, y + h
                print(f"Selected region: ({left}, {top}) → ({right}, {bottom})")

                string_id = input("Enter ExpectedStringID for this region: ").strip()
                if not string_id:
                    print("Canceled. Try again.")
                    continue

                writer.writerow([step_id, screen_id, string_id, left, top, right, bottom])
                print(f"Saved: {step_id} | {screen_id} | {string_id} | ({left}, {top}, {right}, {bottom})")

                cont = input("Annotate another region on this image? (y/n): ").strip().lower()
                if cont != 'y':
                    break

if __name__ == "__main__":
    run_annotation()