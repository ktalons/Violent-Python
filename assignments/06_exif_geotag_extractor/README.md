# 06 – EXIF Geotag Extractor

Goals
- Extract EXIF GPS data from JPEG images in a chosen directory and present it in a table.
- Export two CSVs: a full dump and a MapMaker-ready subset with coordinates.

Approach
- Use Pillow to read EXIF, decode GPSInfo, and convert DMS to decimal degrees.
- Display results in a PrettyTable and write CSVs for further mapping/analysis.

Defaults and interaction
- On start, prints a default directory and prompts for input.
- Press Enter to use the default (assets/testImages when present) or enter a custom path.
- Only .jpg/.jpeg files are processed.

Results
- Prints a table with columns: File, Lat, Lon, Timestamp, Make, Model.
- Writes the following files:
  - output/imageGPSfull.csv (all rows)
  - output/imageGPSmapmaker.csv (rows with coordinates only)

Dependencies
```bash
python3 -m pip install pillow prettytable
```

Run
```bash
python3 assignments/06_exif_geotag_extractor/06_exif_geotag_extractor.py
```
