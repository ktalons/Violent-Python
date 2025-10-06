# Kyle Versluis, 09/26/2025, Assignment 5
# Title: Searching for Digital Images with Python
# Purpose: Extracts EXIF GPS data from JPEG images in a specified folder
#          and outputs the results in a table and CSV files for mapping.
"""
Requires Python 3.6+
3rd party dependencies:
pip install pillow prettytable
"""

import os                                               # For filesystem operations
import sys                                              # For exit()
import csv                                              # For CSV writing
from datetime import datetime                           # For timestamping
from typing import Dict, List, Optional, Tuple, Any     # For type hints
from pathlib import Path                                 # For path manipulations

from PIL import Image                                   # For image processing
from PIL.ExifTags import TAGS, GPSTAGS                  # For EXIF tag decoding
from prettytable import PrettyTable                     # For table printing

# Helper function to find the default directory relative to this script.
"""
Return the default directory path for test images. This function
attempts to locate the 'assets/testImages' directory relative
to the script's location, accommodating various project structures.
If the directory cannot be found, it defaults to the current working directory.
"""
def repo_default_dir() -> Path:
    script = Path(__file__).resolve()

    # Attempts to find the repo root by looking for a .git folder
    for parent in script.parents:
        repo_path = parent / "assets" / "testImages"
        if repo_path.is_dir():
            return repo_path

        # If we find a repo root marker, use it even if the folder isn't created yet
        if (parent / ".git").exists():
            return parent / "assets" / "testImages"

    # Fallback if no repo root found
    return Path.cwd()

DEFAULT_DIR = repo_default_dir()
print(f"[info] Using default directory: {DEFAULT_DIR}")
# --------------------------------------------------------------------------

# Helper function to prompt for directory with retries
# Prompts user up to `attempts` times for a valid directory path.
# User can press Enter to use default or type 'quit' to exit.
# Returns a valid directory path or exits the program.
def directorySelector(default_dir: Path, attempts: int =2) -> Path:
    for i in range(attempts):
        prompt = (
            "Enter a path to a directory of JPEGs to search\n"
            f"[Press Enter for default: {default_dir}] or type \'quit\' to exit\n"
            "Directory path: "
        )
        user_in = input(prompt).strip()
        # Handle quit request
        if user_in.lower() in {'q', 'quit', 'exit'}:
            print("Okay, exiting as requested.")
            sys.exit(0)
        # Use default if input is empty
        folder = Path(user_in).expanduser().resolve() if user_in else Path(default_dir).resolve()

        if folder.is_dir():
            return folder

        # If invalid and another attempt remains, inform the user.
        if i < attempts - 1:
            print("That wasn't a valid directory:\n  {folder}\nPlease try again.\n")

    # Out of attempts.
    print("ERROR: No valid directory provided. Exiting.")
    sys.exit(1)

# Helper functions for EXIF GPS extraction
# Rational2Float: (numerator, denominator) -> float
def Rational2Float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        pass
    try:
        num, den = x
        return float(num) / float(den) if float(den) != 0 else 0.0
    except Exception:
        return float(x) if x is not None else 0.0

# Dms2Decimal: (degrees, minutes, seconds) -> decimal degrees
def Dms2Decimal(dms: Tuple[Any, Any, Any], ref: str) -> float:
    degrees = Rational2Float(dms[0])
    minutes = Rational2Float(dms[1])
    seconds = Rational2Float(dms[2]) if len(dms) > 2 else 0.0
    # Calculates decimal degrees
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal

# ExtractGPSDictionary: (image path) -> (GPS dictionary, basic info)
def ExtractGPSDictionary(img_path: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    imageTimeStamp = "NA"
    cameraMake = "NA"
    cameraModel = "NA"
    gpsData = None
    # Open image
    try:
        with Image.open(img_path) as im:
            exif = im._getexif()
    except Exception:
        return None, [imageTimeStamp, cameraMake, cameraModel]
    if not exif:
        return None, [imageTimeStamp, cameraMake, cameraModel]

    # Decode EXIF keys and pull basics + GPS block
    for tag_id, value in exif.items():
        tag = TAGS.get(tag_id, tag_id)
        # strip() to remove any whitespace/newlines
        if tag == "DateTimeOriginal":
            try:
                imageTimeStamp = str(value).strip()
            except Exception:
                pass
        elif tag == "Make":
            try:
                cameraMake = str(value).strip()
            except Exception:
                pass
        elif tag == "Model":
            try:
                cameraModel = str(value).strip()
            except Exception:
                pass
        elif tag == "GPSInfo":
            gpsData = {}
            for key in value:
                gpsTag = GPSTAGS.get(key, key)
                gpsData[gpsTag] = value[key]

    return gpsData, [imageTimeStamp, cameraMake, cameraModel]
# End ExtractGPSDictionary ==================================

# Extract Lat Lon: (GPS dictionary) -> (lat, lon, latRef, lonRef)
def ExtractLatLon(gps: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not gps:
        return None
    # Extract relevant fields
    try:
        lat = gps["GPSLatitude"]
        latRef = gps["GPSLatitudeRef"]
        lon = gps["GPSLongitude"]
        lonRef = gps["GPSLongitudeRef"]

        lat_dd = Dms2Decimal(lat, latRef)
        lon_dd = Dms2Decimal(lon, lonRef)

        return {"lat": lat_dd, "lon": lon_dd, "lat_ref": latRef, "lon_ref": lonRef}
    except Exception:
        return None
# End Extract Lat Lon ==============================================

# ------------------------- MAIN LOGIC ---------------------------------- #
# Find JPEG images in a folder (case-insensitive .jpg/.jpeg)
def findImages(folder: str) -> List[str]:
    exts = {".jpg", ".jpeg"}
    out = []
    for name in sorted(os.listdir(folder)):
        p = os.path.join(folder, name)
        if os.path.isfile(p) and os.path.splitext(name.lower())[1] in exts:
            out.append(p)
    return out

# Returns a list of rows with extracted data
def processFolder(folder: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    images = findImages(folder)

    for gpsPath in images:
        gps, basics = ExtractGPSDictionary(gpsPath)
        timestamp, make, model = basics
        lat = lon = None
        if gps:
            gpsCoordinates = ExtractLatLon(gps)
            if gpsCoordinates:
                lat = gpsCoordinates["lat"]
                lon = gpsCoordinates["lon"]

        rows.append(
            {
                "file": os.path.basename(gpsPath),
                "timestamp": timestamp,
                "make": make,
                "model": model,
                "lat": lat,
                "lon": lon,
            }
        )
    return rows

# Writes a CSV formatted for MapMaker import
def mapmakerCSVwriter(rows: List[Dict[str, Any]], out_path: str) -> None:

    fieldnames = [
        "Title",
        "Latitude",
        "Longitude",
        "Description",
        "Timestamp",
        "Make",
        "Model",
        "Filename",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            if r["lat"] is None or r["lon"] is None:
                # Skip rows with no coordinates for the map CSV
                continue
            w.writerow(
                {
                    "Title": r["file"],
                    "Latitude": f'{r["lat"]:.6f}',
                    "Longitude": f'{r["lon"]:.6f}',
                    "Description": f'{r["make"]} {r["model"]} @ {r["timestamp"]}',
                    "Timestamp": r["timestamp"],
                    "Make": r["make"],
                    "Model": r["model"],
                    "Filename": r["file"],
                }
            )

# Pretty-print results in a table
def tablePrint(rows: List[Dict[str, Any]]) -> None:
    resultsTable = PrettyTable(["File", "Lat", "Lon", "Timestamp", "Make", "Model"])
    for r in rows:
        lat = f'{r["lat"]:.6f}' if r["lat"] is not None else "—"
        lon = f'{r["lon"]:.6f}' if r["lon"] is not None else "—"
        resultsTable.add_row([r["file"], lat, lon, r["timestamp"], r["make"], r["model"]])
    print(resultsTable)


# Main function
# ------------------------- ENTRY POINT ---------------------------------- #
# prints title and start time of the script
def main():
    print("\nExtract EXIF Data from JPEGs")
    print("Script Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    # Ask user for directory, falls back to DEFAULT_DIR if they press Enter
    folder = directorySelector(str(DEFAULT_DIR))
    print(f"\nSearching for JPEG images in:\n  {folder}\n")

    images = findImages(folder)
    if not images:
        print("No images found in that folder. Must be .jpg/.jpeg format")
        sys.exit(0)

    rows = processFolder(folder)

    # Show results
    print()
    tablePrint(rows)

    # Write CSVs
    os.makedirs("output", exist_ok=True)
    map_csv = os.path.join("output", "imageGPSmapmaker.csv")
    full_csv = os.path.join("output", "imageGPSfull.csv")

    # Full CSV with all rows (including those without GPS)
    with open(full_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Filename", "Latitude", "Longitude", "Timestamp", "Make", "Model"])
        for r in rows:
            w.writerow(
                [
                    r["file"],
                    f'{r["lat"]:.6f}' if r["lat"] is not None else "",
                    f'{r["lon"]:.6f}' if r["lon"] is not None else "",
                    r["timestamp"],
                    r["make"],
                    r["model"],
                ]
            )

    # MapMaker-ready CSV (only rows with coordinates)
    mapmakerCSVwriter(rows, map_csv)

    print("\nFiles written:")
    print(" -", os.path.abspath(full_csv))
    print(" -", os.path.abspath(map_csv))
    print("\nUpload imageGPSmapmaker.csv to MapMaker to plot points.")


if __name__ == "__main__":
    main()
